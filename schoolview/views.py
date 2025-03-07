from django.db import transaction
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponse
from school.models import *
from django.contrib.auth import logout
from schoolview.forms import UserRegisterForm, EditProfileForm
import random
from datetime import datetime, date, timedelta
from django.db.models.fields.files import ImageFieldFile, FileField
from django.contrib.auth.decorators import login_required
from django.db.models import F, ExpressionWrapper, IntegerField
from django.views import View
from django.urls import reverse_lazy
from school.models import Subquestion, Right_answer, Wrong_answer
from .forms import *


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
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
            (((F('practice__zero') * 2) - 1) * (F('practice__nf') + 1) / (F('practice__nt') + 1)),
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
    questions_data = request.session.get('questions_data', {})

    correct_answered = {}
    wrong_answered = {}

    for key, correct_answer in correct_answers_sesh.items():
        user_answer = user_answers.get(key, '')

        # اطلاعات سوال مربوطه
        question_data = questions_data.get(key, {})
        question_text = question_data.get("question_text", "سوال یافت نشد")
        subquestion_text = question_data.get("subquestion_text", "")

        # اگر جواب صحیح داده شده
        if user_answer == correct_answer:
            correct_answered[key] = {
                "question": question_text,
                "subquestion": subquestion_text,
                "user_answer": user_answer
            }
        else:
            wrong_answered[key] = {
                "question": question_text,
                "subquestion": subquestion_text,
                "user_answer": user_answer,
                "correct_answer": correct_answer
            }

    wrong_answers_count = len(wrong_answered)
    darsad = (len(correct_answered) / (len(correct_answered) + wrong_answers_count)) * 100 if (
                correct_answered or wrong_answers_count) else 0

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
        correct_answers_from_db = set(
            Right_answer.objects.filter(subquestion=subquestion).values_list('title', flat=True))
        existing_practice = Practice.objects.filter(subquestion=subquestion).first()

        # practice
        if not existing_practice:
            nt = nf = zero = 0
            try:
                if correct_answered[key] in correct_answers_from_db:
                    nt += 1
                    zero = 0

            except KeyError:
                nf += 1
                zero += 1

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
                    existing_practice.nt += 1
                    existing_practice.zero = 0
                    existing_practice.date = date.today()
                    existing_practice.save()

            except KeyError:
                existing_practice.nf += 1
                existing_practice.zero += 1
                existing_practice.date = date.today()
                existing_practice.save()

    # worksheet
    worksheet, created = Question_practice_worksheet.objects.get_or_create(
        student=student, date=date.today(), defaults={"total_time": 0, "time_spent": 0}
    )

    worksheet.total_time += exam_data.get('total_time', 0)
    worksheet.time_spent += 20
    worksheet.save()
    request.session.pop('exam_data', None)
    request.session.pop('questions_data', None)
    request.session.pop('correct_answers', None)
    request.session.pop('user_answers', None)
    request.session.pop('wrong_answered', None)
    request.session.pop('correct_answered', None)

    return HttpResponse({"Worksheet saved successfully!"})


class LeitnerView(View):
    def __init__(self):
        super().__init__()
        self.questions_data = {}
        self.correct_answers = {}

    def upgrade_subquestions(self, student):
        leitner = Leitner.objects.filter(student=student).first()
        leitner_questions = []
        # leitner_question = None

        if leitner.last_step == 1:
            leitner_questions = Leitner_question.objects.filter(n__range=(15, 29))
        elif leitner.last_step == 2:
            leitner_questions = Leitner_question.objects.filter(n__range=(7, 13))
        elif leitner.last_step == 3:
            leitner_questions = Leitner_question.objects.filter(n__range=(3, 5))
        elif leitner.last_step == 4:
            leitner_questions = Leitner_question.objects.filter(n=1)
        elif leitner.last_step == 5:
            print(5)
            leitner_questions = Leitner_question.objects.filter(n=-1)

        if leitner_questions:
            try:
                for question in leitner_questions:
                    print(question.n)
                    question.n += 1
                    question.save()

            except AttributeError:
                pass

    def get(self, request):

        student = Student.objects.get(student=request.user)
        try:
            leitner, created = Leitner.objects.get_or_create(student=student)
        except KeyError:
            return HttpResponse({"error": "leitner not found"}, status=404)

        # find student  personal leitner
        if leitner.last_step == 1 and leitner.datel == date.today():
            return HttpResponse({"error": "you have done your letner for today"}, status=404)

        numbers = (30, 14, 6, 2, 0)
        if leitner.last_step > 5:
            leitner.last_step = 1
            leitner.datel = date.today()
            # add upgrades here
            self.upgrade_subquestions(student)
            leitner.save()
            return redirect('schoolview:index')
        subquestions = Subquestion.objects.filter(leitner_question__n=numbers[(leitner.last_step) - 1])

        if not subquestions:
            self.upgrade_subquestions(student)
            leitner.last_step += 1
            leitner.datel = date.today()
            leitner.save()
            return redirect('schoolview:leitner')
        else:
            for idx, subquestion in enumerate(subquestions, start=1):
                correct_answer = Right_answer.objects.filter(subquestion=subquestion).order_by('?').first()
                wrong_answers = list(Wrong_answer.objects.filter(subquestion=subquestion).order_by('?')[:3])
                all_answers = [correct_answer] + wrong_answers
                random.shuffle(all_answers)

                key = f"question_{idx}"
                self.questions_data[key] = {
                    "subquestion_number": str(idx),
                    "subquestion_id": subquestion.id,
                    "question_text": subquestion.question.title,
                    "subquestion_text": subquestion.text,
                    "subquestion_image": serialize_value(subquestion.image),
                    "answers": [{"text": ans.title, "is_correct": ans == correct_answer} for ans in all_answers]
                }
                self.correct_answers[key] = correct_answer.title
                request.session['questions_data'] = self.questions_data
                request.session['correct_answers'] = self.correct_answers
            return render(request, "school/leitner.html", {'questions_data': self.questions_data,
                                                           'leitner': leitner.last_step, })

    def post(self, request):
        student = Student.objects.get(student=request.user)
        questions_data = request.session.get("questions_data")
        correct_answers = request.session.get("correct_answers")
        user_answers = {key: request.POST.get(key) for key in request.session.get('correct_answers', {})}
        for key in user_answers:
            if key in correct_answers:  # Ensure the key exists in both dictionaries

                value1 = user_answers[key]
                value2 = correct_answers[key]

                practice = Practice.objects.filter(subquestion__id=questions_data[key]['subquestion_id']).first()

                leitner_question = Leitner_question.objects.get(
                    subquestion_id=questions_data[key]['subquestion_id']
                )

                leitner = Leitner.objects.filter(student=student).first()

                if value1 == value2:
                    # practice
                    practice.zero = 0
                    practice.nt += 1
                    practice.date = date.today()
                    practice.save()

                    # leitner_question
                    leitner_question.n += 1
                    leitner_question.datelq = date.today()
                    leitner_question.save()

                    leitner.last_step += 1
                    leitner.datel = date.today()
                    leitner.save()


                else:
                    # practice
                    practice.zero += 1
                    practice.nf += 1
                    practice.date = date.today()
                    practice.save()

                    # leitner_question
                    leitner_question.n = -1
                    leitner_question.datelq = date.today()
                    leitner_question.save()

                    leitner.last_step += 1
                    leitner.datel = date.today()
                    leitner.save()

        self.upgrade_subquestions(student)

        return redirect('schoolview:leitner')


@login_required(login_url='/login/')
def student_profile(request, user_id):
    student = Student.objects.get(student=user_id)
    leitner = Leitner.objects.filter(student=student).first()
    leitner_question = Leitner_question.objects.filter(student=student)
    question_practice_worksheet = Question_practice_worksheet.objects.filter(student=student)
    current_date = date.today()
    worksheets = Question_practice_worksheet.objects.filter(student=student)

    context = {
        'student': student,
        'leitner': leitner,
        'leitner_question': leitner_question,
        'question_practice_worksheet': question_practice_worksheet,
        'current_date': current_date,
        'worksheets': worksheets,
    }
    return render(request, 'school/student_profile.html', context)


@login_required(login_url='/login/')
def designer_profile(request, user_id):
    designer = Question_designer.objects.get(designer=user_id)
    context = {
        'designer': designer,
    }
    return render(request, 'school/designer_profile.html', context)


@login_required(login_url='/login/')
def edit_profile(request):
    if request.method == 'POST':
        user_form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if user_form.is_valid():
            user_form.save()
    else:
        user_form = EditProfileForm(instance=request.user)
    context = {
        'user_form': user_form,
    }
    return render(request, 'registration/edit_profile.html', context)


@login_required(login_url='/login/')
def questions(request, user_id):
    student = Student.objects.get(student=user_id)
    questions = Practice.objects.filter(student=student)
    return render(request, "school/questions.html", {'questions': questions})


def designer_subquestions(request, user_id):
    question_designer = get_object_or_404(Question_designer, designer_id=user_id)
    subquestions = Subquestion.objects.filter(question_designer=question_designer)
    context = {
        'question_designer': question_designer,
        'subquestions': subquestions,
    }
    return render(request, 'school/designer_subquestions.html', context)

@login_required(login_url='/login/')
def subquestion_create_view(request):
    question_designer = get_object_or_404(Question_designer, designer=request.user)

    if request.method == "POST":
        form = SubquestionForm(request.POST, request.FILES)
        if form.is_valid():
            subquestion = form.save(commit=False)
            subquestion.question_designer = question_designer
            subquestion.save()
            form.save_m2m()
            return redirect("schoolview:right_answer_create", subquestion_id=subquestion.id)

    elif request.method == "GET":
        form = SubquestionForm()
    return render(request, 'forms/subquestion_form.html', {'form': form})
    # return redirect("schoolview:index")


@login_required(login_url='/login/')
def right_answer_create_view(request, subquestion_id):
    subquestion = Subquestion.objects.get(id=subquestion_id)

    if request.method == "POST":
        formset = RightAnswerFormSet(request.POST, request.FILES)
        if formset.is_valid():
            answers = formset.save(commit=False)
            for answer in answers:
                answer.subquestion = subquestion
                answer.save()
            print(subquestion.id)
            return redirect('schoolview:wrong_answer_create', subquestion_id=subquestion.id)
    else:
        formset = RightAnswerFormSet(queryset=Right_answer.objects.filter(subquestion=subquestion))

    return render(request, 'forms/right_answer_form.html', {'formset': formset, 'subquestion': subquestion})


@login_required(login_url='/login/')
def wrong_answer_create_view(request, subquestion_id):
    subquestion = Subquestion.objects.get(id=subquestion_id)

    if request.method == "POST":
        formset = WrongAnswerFormSet(request.POST, request.FILES)
        if formset.is_valid():
            answers = formset.save(commit=False)
            for answer in answers:
                answer.subquestion = subquestion
                answer.save()
            return redirect('schoolview:index')
    else:
        formset = WrongAnswerFormSet(queryset=Wrong_answer.objects.filter(subquestion=subquestion))

    return render(request, 'forms/wrong_answer_form.html', {'formset': formset, 'subquestion': subquestion})


@login_required(login_url='/login/')
def create_full_hierarchy_view(request):
    question_designer = get_object_or_404(Question_designer, designer=request.user)

    if request.method == "POST":
        # مقادیر را از request.POST دریافت می‌کنیم
        course_name = request.POST.get("course_name")
        book_name = request.POST.get("book_name")
        season_name = request.POST.get("season_name")
        lesson_name = request.POST.get("lesson_name")
        subject_name = request.POST.get("subject_name")

        course = Course.objects.create(name=course_name, designer=question_designer)

        book = Book.objects.create(name=book_name, course=course)

        season = Season.objects.create(name=season_name, book=book)

        lesson = Lesson.objects.create(name=lesson_name, season=season)

        Subject.objects.create(name=subject_name, lesson=lesson)

        return redirect('schoolview:index')

    return render(request, 'forms/create_full_hierarchy.html')


def designer_questions(request, user_id):
    question_designer = get_object_or_404(Question_designer, designer_id=user_id)
    questions = Question.objects.all()
    return render(request, "school/designer_questions.html", {'questions': questions})

def create_question(request):
    get_object_or_404(Question_designer, designer=request.user)
    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('schoolview:index')
    else:
        form = QuestionForm()
    return render(request, 'forms/create_question.html', {'form': form})


def edit_subquestion(request, subquestion_id):
    subquestion = get_object_or_404(Subquestion, id=subquestion_id)
    right_answers = Right_answer.objects.filter(subquestion=subquestion)
    wrong_answers = Wrong_answer.objects.filter(subquestion=subquestion)

    if request.method == "POST":
        subquestion_form = SubquestionForm(request.POST, request.FILES, instance=subquestion)
        right_answer_forms = [RightAnswerForm(request.POST, request.FILES, prefix=str(i), instance=answer) for i, answer in enumerate(right_answers)]
        wrong_answer_forms = [WrongAnswerForm(request.POST, request.FILES, prefix=str(i), instance=answer) for i, answer in enumerate(wrong_answers)]

        if subquestion_form.is_valid() and all(form.is_valid() for form in right_answer_forms + wrong_answer_forms):
            subquestion_form.save()
            for form in right_answer_forms + wrong_answer_forms:
                form.save()
            return redirect('schoolview:designer_subquestions', request.user.id)

    else:
        subquestion_form = SubquestionForm(instance=subquestion)
        right_answer_forms = [RightAnswerForm(prefix=str(i), instance=answer) for i, answer in enumerate(right_answers)]
        wrong_answer_forms = [WrongAnswerForm(prefix=str(i), instance=answer) for i, answer in enumerate(wrong_answers)]

    return render(request, 'forms/edit_subquestion.html', {
        'subquestion_form': subquestion_form,
        'right_answer_forms': right_answer_forms,
        'wrong_answer_forms': wrong_answer_forms,
        'subquestion': subquestion
    })