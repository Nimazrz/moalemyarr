from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import HttpResponse
from school.models import *
from django.contrib.auth import logout
from schoolview.forms import UserRegisterForm
import random
from urllib.parse import urlencode
from django.forms.models import model_to_dict
from datetime import datetime, date, timedelta
from django.db.models.fields.files import ImageFieldFile, FileField
from django.contrib.auth.decorators import login_required
from datetime import date

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

        for idx, subquestion in enumerate(subquestions, start=1):
            correct_answer = Right_answer.objects.filter(subquestion=subquestion).order_by('?').first()
            wrong_answers = list(Wrong_answer.objects.filter(subquestion=subquestion).order_by('?')[:3])
            all_answers = [correct_answer] + wrong_answers
            random.shuffle(all_answers)

            key = f"question_{idx}"
            questions_data[key] = {
                "subquestion_number": str(idx),
                "question_text": subquestion.question.title,
                "subquestion_text": subquestion.text,
                # "subquestin": serialize_model(subquestion),
                "subquestion_image": serialize_value(subquestion.image),
                "subquestion_time": serialize_value(subquestion.time),
                "answers": [{"text": ans.title, "is_correct": ans == correct_answer} for ans in all_answers]
            }

            correct_answers[key] = correct_answer.title

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
    questions_data = request.session.get('questions_data')
    correct_answers_sesh = request.session.get('correct_answers')
    user_answers = request.session.get('user_answers')
    # request.session.clear()

    for key in user_answers:
        if user_answers[key] == correct_answers_sesh[key]:
            correct_answered[f"{key}"] = correct_answers_sesh[f"{key}"]
        else:
            wrong_answered[f"{key}"] = user_answers[f"{key}"]
            wrong_answered[f"correct_answer_{key}"] = correct_answers_sesh[f"{key}"]
    
    all_time = sum(float(q["subquestion_time"]) for q in questions_data.values())

    wrong_answers_wothot_corrects = [key for key in wrong_answered if key.startswith('correct_answer_')]
    context = {
        'correct_answered': correct_answered,
        'wrong_answered': wrong_answered,
        'correct_answered_count': len(correct_answered),
        'wrong_answered_count': len(wrong_answers_wothot_corrects),
        'all_time':all_time,
        'darsad': ((len(correct_answered))/(len(correct_answered)+len(wrong_answers_wothot_corrects)))*100,
    }
    return render(request, 'school/worksheet.html', context)


from django.http import JsonResponse
from school.models import Student, Question_practice_worksheet

def save_worksheet(request):
    if request.method == "POST":
        student = request.user

        try:
            # بررسی اینکه آیا کاربر لاگین کرده است
            if not student.is_authenticated:
                return JsonResponse({"error": "User is not authenticated"}, status=401)

            # گرفتن نمونه `Student` از روی `request.user`
            student = Student.objects.filter(student=student).first()
            if not student:
                return JsonResponse({"error": "Student profile not found"}, status=404)

            # ذخیره Worksheet
            worksheet = Question_practice_worksheet.objects.create(student=student)
            worksheet.save()

            return JsonResponse({"message": "Worksheet saved successfully!"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
