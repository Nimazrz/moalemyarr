from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import HttpResponse
from school.models import *
from django.contrib.auth import logout
from schoolview.forms import UserRegisterForm
import random
from urllib.parse import urlencode

# Create your views here.

from django.shortcuts import render
from django.http import HttpResponse
from .forms import UserRegisterForm


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


def exam(request):
    questions_data = []
    correct_answers = {}
    subquestions = Subquestion.objects.all()

    for idx, subquestion in enumerate(subquestions, start=1):
        correct_answer = Right_answer.objects.filter(subquestion=subquestion).order_by('?').first()
        wrong_answers = list(Wrong_answer.objects.filter(subquestion=subquestion).order_by('?')[:3])
        print(correct_answer)
        all_answers = [correct_answer] + wrong_answers
        random.shuffle(all_answers)
        request.session['correct_answers'] = correct_answers
        questions_data.append({
            "question_number": f"{idx}",
            "question": subquestion.question,
            "subquestion": subquestion,
            "answers": [{"text": ans.title, "is_correct": ans == correct_answer} for ans in all_answers]
        })
        correct_answers[f"question_{idx}"] = correct_answer.title

    if request.method == 'POST':
        user_answers = {}
        for idx, question in enumerate(questions_data, start=1):
            selected_answer = request.POST.get(f"question_{idx}")
            user_answers[f"question_{idx}"] = selected_answer

        request.session['user_answers'] = user_answers

        print("hi")
        print(correct_answers)
        print(user_answers)
        return redirect(reverse('schoolview:worksheet'))

    return render(request, "school/exam.html", {"questions_data": questions_data})


def make_worksheet(request):
    correct_answered = []
    wrong_answered = []
    correct_answers = request.session.get('correct_answers')
    user_answers = request.session.get('user_answers')
    request.session.clear()

    for key in user_answers:
        if user_answers[key] == correct_answers[key]:
            correct_answered.append(f"question_{key}")
        else:
            wrong_answered.append(f"question_{key}")
    context = {
        'correct_answered': correct_answered,
        'wrong_answered': wrong_answered,
        'correct_answered_count': len(correct_answered),
        'wrong_answers_count': len(wrong_answered),
    }
    return render(request, 'school/worksheet.html', context)
