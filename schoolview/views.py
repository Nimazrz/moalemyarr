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

def make_worksheet(request):
    correct_answered = {}
    wrong_answered = {}
    questions_data = request.session.get('questions_data')
    correct_answers_sesh = request.session.get('correct_answers')
    user_answers = request.session.get('user_answers')
    request.session.clear()

    for key in user_answers:
        if user_answers[key] == correct_answers_sesh[key]:
            correct_answered[f"{key}"] = correct_answers_sesh[f"{key}"]
        else:
            wrong_answered[f"{key}"] = user_answers[f"{key}"]
            wrong_answered[f"correct_answer_{key}"] = correct_answers_sesh[f"{key}"]
    
    all_time = sum(float(q["subquestion_time"]) for q in questions_data.values())


    context = {
        'correct_answered': correct_answered,
        'wrong_answered': wrong_answered,
        'correct_answered_count': len(correct_answered),
        'wrong_answers_count': len(wrong_answered),
        'all_time':all_time,
    }
    return render(request, 'school/worksheet.html', context)
