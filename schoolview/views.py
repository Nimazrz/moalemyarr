from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import HttpResponse
from school.models import *
from django.contrib.auth import logout
from schoolview.forms import UserRegisterForm
import random
from django.forms.models import model_to_dict
from datetime import datetime, date, timedelta
from django.db.models.fields.files import ImageFieldFile, FileField
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist



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


def serialize_model(model_instance):
    """Convert a Django model instance into a JSON-serializable dictionary."""
    model_dict = model_to_dict(model_instance)  # Convert model to dict
    return {key: serialize_value(value) for key, value in model_dict.items()}  # Serialize all values


@login_required
def exam(request):
    correct_answers = {}
    subquestions = Subquestion.objects.all()

    if request.method == 'GET':
        questions_data = {}
        exam_data = {}
        total_time = 0

        for idx, subquestion in enumerate(subquestions, start=1):
            correct_answer = Right_answer.objects.filter(subquestion=subquestion).order_by('?').first()
            wrong_answers = list(Wrong_answer.objects.filter(subquestion=subquestion).order_by('?')[:3])
            all_answers = [correct_answer] + wrong_answers
            random.shuffle(all_answers)

            key = f"question_{idx}"
            questions_data[key] = {
                "subquestion_number": str(idx),
                'subquestion_id': subquestion.id,
                "question_text": subquestion.question.title,
                "subquestion_text": subquestion.text,
                # "subquestin": serialize_model(subquestion),
                "subquestion_image": serialize_value(subquestion.image),
                "subquestion_time": subquestion.time,

                "answers": [{"text": ans.title, "is_correct": ans == correct_answer} for ans in all_answers]
            }

            total_time += subquestion.time
            correct_answers[key] = correct_answer.title
        exam_data['total_time'] = total_time
        request.session['exam_data'] = exam_data
        request.session['questions_data'] = questions_data
        request.session['correct_answers'] = correct_answers
        request.session.modified = True

        return render(request, "school/exam.html", {"questions_data": questions_data})

    elif request.method == 'POST':
        correct_answers = request.session.get('correct_answers', {})
        user_answers = {}

        for key in correct_answers.keys():
            selected_answer = request.POST.get(key)
            user_answers[key] = selected_answer

        request.session['user_answers'] = user_answers
        request.session.modified = True

        return redirect(reverse('schoolview:worksheet'))


@login_required(login_url='/exam/')
def make_worksheet(request):
    correct_answered = {}
    wrong_answered = {}
    exam_data = request.session.get('exam_data')
    questions_data = request.session.get('questions_data')
    correct_answers_sesh = request.session.get('correct_answers')
    user_answers = request.session.get('user_answers')

    for key in user_answers:
        if user_answers[key] == correct_answers_sesh[key]:
            correct_answered[f"{key}"] = correct_answers_sesh[f"{key}"]
        else:
            wrong_answered[f"{key}"] = user_answers[f"{key}"]
            wrong_answered[f"correct_answer_{key}"] = correct_answers_sesh[f"{key}"]
    
    request.session['wrong_answered'] = wrong_answered
    request.session['correct_answered'] = correct_answered

    wrong_answers_without_corrects = [key for key in wrong_answered if key.startswith('correct_answer_')]
    context = {
        'correct_answered': correct_answered,
        'wrong_answered': wrong_answered,
        'correct_answered_count': len(correct_answered),
        'wrong_answered_count': len(wrong_answers_without_corrects),
        'exam_data': exam_data,
        'darsad': ((len(correct_answered)) / (len(correct_answered) + len(wrong_answers_without_corrects))) * 100,
    }
    return render(request, 'school/worksheet.html', context)


def save_worksheet(request):
    if request.method == "POST":
        exam_data = request.session.get('exam_data')
        questions_data = request.session.get('questions_data')
        studentt = request.user
        student = Student.objects.get(student=studentt)
        worksheet = Question_practice_worksheet.objects.filter(student=student, date=date.today()).first()
     
        # save_practice
        try:
            correct_answered = request.session.get('correct_answered', [])
        except AttributeError:
            correct_answered = {}
            return correct_answered

        for key, value in questions_data.items():
            subquestion = Subquestion.objects.get(id=questions_data[key]['subquestion_id'])
            correct_answers_from_db = list(Right_answer.objects.filter(subquestion=subquestion).values_list('title', flat=True))
            existing_practice = Practice.objects.filter(subquestion=subquestion).first()
        
            if not existing_practice:

                nt = nf = 0
                try:
                    if correct_answered[key] in correct_answers_from_db:
                        nt+=1
                        
                except KeyError:
                    nf +=1

                new_practice = Practice.objects.create(
                    zero=0,
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
                        existing_practice.save()
                        
                except KeyError:
                    existing_practice.nf +=1
                    existing_practice.save()
                    
        # save_worksheet
        if not worksheet:
            
            try:
                if not studentt.is_authenticated:
                    return JsonResponse({"error": "User is not authenticated"}, status=401)

                if not student:
                    return JsonResponse({"error": "Student profile not found"}, status=404)

                worksheet = Question_practice_worksheet.objects.create(student=student,
                                                                       total_time=exam_data['total_time'],
                                                                       date=date.today())
                worksheet.save()

                return HttpResponse({"Worksheet saved successfully!"})

            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

        else:
            worksheet.total_time += exam_data['total_time']
            worksheet.time_spent += 20
            worksheet.save()
            return HttpResponse({"Worksheet updated successfully for today!"})

    return JsonResponse({"error": "Invalid request method"}, status=405)
