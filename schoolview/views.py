from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from school.models import *
from django.contrib.auth import logout
from schoolview.forms import UserRegisterForm
import random
from datetime import datetime, date, timedelta
from django.db.models.fields.files import ImageFieldFile, FileField
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, ExpressionWrapper, IntegerField




def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return render(request, 'registration/register_done.html', {'form': form})
        else:
            return render(request, 'registration/register.html', {'form': form, 'error': 'Form is invalid.'})
    else:
        form = UserRegisterForm()
        return render(request, 'registration/register.html', {'form': form})


def logged_out(request):
    logout(request)
    return render(request, 'registration/logged_out.html')


def index(request):
    questions = Question.objects.all()
    context = {
        'questions': questions
    }
    return render(request, 'school/index.html', context)


def serialize_value(value):
    """Convert non-serializable objects to JSON-serializable formats."""
    if isinstance(value, datetime):
        return value.isoformat()  # Convert datetime to string
    elif isinstance(value, date):
        return value.isoformat()  # Convert date to string
    elif isinstance(value, timedelta):
        return value.total_seconds()  # Convert timedelta to total seconds
    elif isinstance(value, (ImageFieldFile, FileField)):  # Handle image and file fields
        return value.url if value else None  # Get file URL or return None
    return value  # Keep other types as is


@login_required
def exam(request):
    subquestions = Subquestion.objects.annotate(
     total_calculation=ExpressionWrapper(
        (((F('practice__zero')*2)-1)*(F('practice__nf')+F('practice__nt'))),
        output_field=IntegerField())
    ).order_by('-total_calculation')
    if request.method == 'GET':
        questions_data = {}
        exam_data = {"total_time": 0}
        correct_answers = {}

        for idx, subquestion in enumerate(subquestions, start=1):
            correct_answer = Right_answer.objects.filter(subquestion=subquestion).order_by('?').first()
            wrong_answers = list(Wrong_answer.objects.filter(subquestion=subquestion).order_by('?')[:3])
            all_answers = [correct_answer] + wrong_answers
            random.shuffle(all_answers)
            
            key = f"question_{idx}"
            questions_data[key] = {
                "subquestion_number": str(idx),
                "subquestion_id": subquestion.id,
                "question_text": subquestion.question.title,
                "subquestion_text": subquestion.text,
                "subquestion_image": serialize_value(subquestion.image),
                "subquestion_time": subquestion.time,
                "answers": [{"text": ans.title, "is_correct": ans == correct_answer} for ans in all_answers]
            }
            
            exam_data['total_time'] += subquestion.time
            correct_answers[key] = correct_answer.title
        
        request.session.update({
            'exam_data': exam_data,
            'questions_data': questions_data,
            'correct_answers': correct_answers
        })
        return render(request, "school/exam.html", {"questions_data": questions_data})
    
    if request.method == 'POST':
        user_answers = {key: request.POST.get(key) for key in request.session.get('correct_answers', {})}
        request.session['user_answers'] = user_answers
        return redirect(reverse('schoolview:worksheet'))

@login_required(login_url='/exam/')
def make_worksheet(request):
    correct_answers_sesh = request.session.get('correct_answers', {})
    user_answers = request.session.get('user_answers', {})
    correct_answered = {k: v for k, v in correct_answers_sesh.items() if user_answers.get(k) == v}
    wrong_answered = {k: user_answers.get(k, '') for k in correct_answers_sesh if user_answers.get(k) != correct_answers_sesh[k]}
    
    for key in list(wrong_answered.keys()): 
        wrong_answered[f"correct_answer_{key}"] = correct_answers_sesh[key]
    
    request.session.update({
        'wrong_answered': wrong_answered,
        'correct_answered': correct_answered
    })
    
    wrong_answers_count = sum(1 for key in wrong_answered if key.startswith('correct_answer_'))
    darsad = (len(correct_answered) / (len(correct_answered) + wrong_answers_count)) * 100 if correct_answered or wrong_answers_count else 0
    context = {
        'correct_answered': correct_answered,
        'wrong_answered': wrong_answered,
        'correct_answered_count': len(correct_answered),
        'wrong_answered_count': wrong_answers_count,
        'exam_data': request.session.get('exam_data', {}),
        'darsad': darsad
    }
    return render(request, 'school/worksheet.html', context)


@login_required(login_url='/exam/')
def save_worksheet(request):
    if request.method != "POST":
        return HttpResponse({"error": "Invalid request method"}, status=405)
    
    student = Student.objects.filter(student=request.user).first()
    if not student:
        return HttpResponse({"error": "Student profile not found"}, status=404)
    
    exam_data = request.session.get('exam_data', {})
    questions_data = request.session.get('questions_data', {})
    correct_answered = request.session.get('correct_answered', {})
    
    for key, value in questions_data.items():
        subquestion = Subquestion.objects.get(id=value['subquestion_id'])
        correct_answers_from_db = set(Right_answer.objects.filter(subquestion=subquestion).values_list('title', flat=True))
        existing_practice = Practice.objects.filter(subquestion=subquestion).first()

        # practice
        if not existing_practice:
            nt = nf = zero = 0
            try:
                if correct_answered[key] in correct_answers_from_db:
                    nt+=1
                    zero = 0
                    
            except KeyError:
                nf +=1
                zero +=1

            new_practice = Practice.objects.create(
                zero=zero,
                nf=nf,
                nt=nt,
                date=date.today()
            )
            new_practice.student.add(student)
            new_practice.subquestion.add(subquestion)
            new_practice.save()
        else:
            try:
                if correct_answered[key] in correct_answers_from_db:
                    existing_practice.nt+=1
                    existing_practice.zero = 0
                    existing_practice.date = date.today()
                    existing_practice.save()
                    
            except KeyError:
                existing_practice.nf +=1
                existing_practice.zero +=1
                existing_practice.date = date.today()
                existing_practice.save()
        
    # worksheet
    worksheet, created = Question_practice_worksheet.objects.get_or_create(
        student=student, date=date.today(), defaults={"total_time": 0, "time_spent": 0}
        )
    
    worksheet.total_time += exam_data.get('total_time', 0)
    worksheet.time_spent += 20
    worksheet.save()
    # request.session.pop('exam_data', None)
    # request.session.pop('questions_data', None)
    # request.session.pop('correct_answers', None)
    # request.session.pop('user_answers', None)
    # request.session.pop('wrong_answered', None)
    # request.session.pop('correct_answered', None)
    
    return HttpResponse({"Worksheet saved successfully!"})
