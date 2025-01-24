from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from school.models import *
from django.contrib.auth import logout


# Create your views here.

def logged_out(request):
    logout(request)
    return render(request, 'registration/logged_out.html')


def index(request):
    questions = Question.objects.all()
    context = {
        'questions': questions
    }
    return render(request, 'school/index.html', context)