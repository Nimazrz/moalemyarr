# from turtledemo.bytedesign import Designer

from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from school.models import *
from django.contrib.auth import logout
from schoolview.forms import UserRegisterForm, EditProfileForm
import random
from datetime import datetime, date, timedelta
from django.db.models.fields.files import ImageFieldFile, FileField
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F, ExpressionWrapper, IntegerField
from django.views import View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from school.models import Subquestion, Right_answer, Wrong_answer
from .forms import SubquestionForm, RightAnswerForm, WrongAnswerForm
from django.forms import modelformset_factory


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
    correct_answered = {k: v for k, v in correct_answers_sesh.items() if user_answers.get(k) == v}
    wrong_answered = {k: user_answers.get(k, '') for k in correct_answers_sesh if
                      user_answers.get(k) != correct_answers_sesh[k]}

    for key in list(wrong_answered.keys()):
        wrong_answered[f"correct_answer_{key}"] = correct_answers_sesh[key]

    request.session.update({
        'wrong_answered': wrong_answered,
        'correct_answered': correct_answered
    })

    wrong_answers_count = sum(1 for key in wrong_answered if key.startswith('correct_answer_'))
    darsad = (len(correct_answered) / (
            len(correct_answered) + wrong_answers_count)) * 100 if correct_answered or wrong_answers_count else 0
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


def designer_profile(request, user_id):
    designer = Question_designer.objects.get(designer=user_id)
    context = {
        'designer': designer,
    }
    return render(request, 'school/designer_profile.html', context)


@login_required
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


@login_required
def questions(request, user_id):
    student = Student.objects.get(student=user_id)
    questions = Practice.objects.filter(student=student)
    return render(request, "school/questions.html", {'questions': questions})


@login_required
def subquestion_create_view(request):
    question_designer = Question_designer.objects.get(designer=request.user)  # دریافت طراح سوال

    # فرم‌ست‌های اصلاح‌شده با prefix
    RightAnswerFormSet = modelformset_factory(Right_answer, form=RightAnswerForm, extra=1, can_delete=True)
    WrongAnswerFormSet = modelformset_factory(Wrong_answer, form=WrongAnswerForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = SubquestionForm(request.POST, request.FILES)
        right_answer_formset = RightAnswerFormSet(
            request.POST, request.FILES, queryset=Right_answer.objects.none(), prefix="right_answer"
        )
        wrong_answer_formset = WrongAnswerFormSet(
            request.POST, request.FILES, queryset=Wrong_answer.objects.none(), prefix="wrong_answer"
        )

        if form.is_valid() and right_answer_formset.is_valid() and wrong_answer_formset.is_valid():
            subquestion = form.save(commit=False)
            subquestion.question_designer = question_designer
            subquestion.save()

            # ذخیره جواب‌های درست
            right_answers = right_answer_formset.save(commit=False)
            for right_answer in right_answers:
                right_answer.subquestion = subquestion  # تنظیم ارتباط با سوال
                right_answer.save()

            # ذخیره جواب‌های غلط
            wrong_answers = wrong_answer_formset.save(commit=False)
            for wrong_answer in wrong_answers:
                wrong_answer.subquestion = subquestion  # تنظیم ارتباط با سوال
                wrong_answer.save()

            return redirect(reverse_lazy('schoolview:designer_profile'))

        else:
            print("Errors in formsets:", right_answer_formset.errors, wrong_answer_formset.errors)  # Debugging

    else:
        form = SubquestionForm()
        right_answer_formset = RightAnswerFormSet(queryset=Right_answer.objects.none(), prefix="right_answer")
        wrong_answer_formset = WrongAnswerFormSet(queryset=Wrong_answer.objects.none(), prefix="wrong_answer")

    return render(request, 'forms/subquestion_form.html', {
        'form': form,
        'right_answer_formset': right_answer_formset,
        'wrong_answer_formset': wrong_answer_formset
    })