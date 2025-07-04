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
from django.http import JsonResponse
from .tasks import process_worksheet



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
            if subquestion.question:
                question_text = subquestion.question.title
            else:
                question_text = ""

            key = f"question_{idx}"
            questions_data[key] = {
                "subquestion_number": str(idx),
                "subquestion_id": subquestion.id,
                "question_text": question_text,
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
    request.session['correct_answered'] = correct_answered

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

    user = request.user
    exam_data = request.session.get('exam_data', {})
    questions_data = request.session.get('questions_data', {})
    correct_answered = request.session.get('correct_answered', {})

    process_worksheet.delay(user.id, exam_data, questions_data, correct_answered)

    for key in ['exam_data', 'questions_data', 'correct_answers', 'user_answers', 'wrong_answered', 'correct_answered']:
        request.session.pop(key, None)

    return redirect('schoolview:student_profile', request.user.id)

class LeitnerView(View):
    def __init__(self):
        super().__init__()
        self.questions_data = {}
        self.correct_answers = {}

    def upgrade_subquestions(self, student):
        leitner = Leitner.objects.filter(student=student).first()
        leitner_questions = []
        if leitner.last_step == 1:
            leitner_questions = Leitner_question.objects.filter(n__range=(15, 29))
        elif leitner.last_step == 2:
            leitner_questions = Leitner_question.objects.filter(n__range=(7, 13))
        elif leitner.last_step == 3:
            leitner_questions = Leitner_question.objects.filter(n__range=(3, 5))
        elif leitner.last_step == 4:
            leitner_questions = Leitner_question.objects.filter(n=1)
        elif leitner.last_step >= 5:
            leitner_questions = Leitner_question.objects.filter(n=-1)

        if leitner_questions:
            try:
                for question in leitner_questions:
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
            return HttpResponse({"you have done your leitner for today"}, status=404)

        numbers = (30, 14, 6, 2, 0)
        if leitner.last_step > 5:
            leitner.last_step = 1
            leitner.datel = date.today()
            # add upgrades here
            self.upgrade_subquestions(student)
            leitner.save()
            return redirect('schoolview:index')
        subquestions = Subquestion.objects.filter(leitner_question__n=numbers[(leitner.last_step) - 1],
                                                  leitner_question__student=student)

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
                if subquestion.question:
                    subquestion_question_title = subquestion.question.title
                else:
                    subquestion_question_title = ""

                key = f"question_{idx}"
                self.questions_data[key] = {
                    "subquestion_number": str(idx),
                    "subquestion_id": subquestion.id,
                    "question_text": subquestion_question_title,
                    "subquestion_text": subquestion.text,
                    "subquestion_image": serialize_value(subquestion.image),
                    "subquestion_time": subquestion.time,
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
        subquestion_times = 0
        for key, value in questions_data.items():
            subquestion_times += questions_data[key]['subquestion_time']

        leitner = Leitner.objects.get(student=student)

        for key in user_answers:
            if key in correct_answers:

                value1 = user_answers[key]
                value2 = correct_answers[key]

                practice, created = Practice.objects.get_or_create(
                    subquestion__id=questions_data[key]['subquestion_id'])
                practice.student.add(student)
                practice.subquestion.add(questions_data[key]['subquestion_id'])
                practice.save()

                leitner_question = Leitner_question.objects.filter(
                    student=student,
                    subquestion__text=questions_data[key]['subquestion_text'],
                ).first()

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

        self.upgrade_subquestions(student)

        leitner.last_step += 1
        leitner.datel = date.today()
        leitner.save()

        worksheet, created = Question_practice_worksheet.objects.get_or_create(student=student, date=date.today())
        worksheet.total_time += subquestion_times
        worksheet.save()
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
    students = Student.objects.all().exclude(id=user_id)
    context = {
        'designer': designer,
        'students': students,

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
            return redirect('schoolview:designer_subquestions', request.user.id)
    else:
        formset = WrongAnswerFormSet(queryset=Wrong_answer.objects.filter(subquestion=subquestion))

    return render(request, 'forms/wrong_answer_form.html', {'formset': formset, 'subquestion': subquestion})


@login_required
def ajax_hierarchy_fetch(request):
    fetch_type = request.GET.get("type")
    name = request.GET.get("name", "").strip()
    result = []

    try:
        if fetch_type == "book":
            course = Course.objects.filter(name=name, designer__designer=request.user).first()
            if course:
                result = [{"value": b.name, "label": str(b)} for b in Book.objects.filter(course=course)]

        elif fetch_type == "season":
            book = Book.objects.filter(name=name, course__designer__designer=request.user).first()
            if book:
                result = [{"value": s.name, "label": str(s)} for s in Season.objects.filter(book=book)]

        elif fetch_type == "lesson":
            season = Season.objects.filter(name=name, book__course__designer__designer=request.user).first()
            if season:
                result = [{"value": l.name, "label": str(l)} for l in Lesson.objects.filter(season=season)]

        elif fetch_type == "subject":
            lesson = Lesson.objects.filter(name=name, season__book__course__designer__designer=request.user).first()
            if lesson:
                result = [{"value": s.name, "label": str(s)} for s in Subject.objects.filter(lesson=lesson)]

    except Exception:
        result = []

    return JsonResponse({"result": result})


@login_required(login_url='/login/')
def create_full_hierarchy_view(request):
    question_designer = get_object_or_404(Question_designer, designer=request.user)

    courses = Course.objects.filter(designer=question_designer)

    books = Book.objects.filter(course__in=courses)
    seasons = Season.objects.filter(book__in=books)
    lessons = Lesson.objects.filter(season__in=seasons)
    subjects = Subject.objects.filter(lesson__in=lessons)

    if request.method == "POST":
        course_name = request.POST.get("course_name", "").strip()
        book_name = request.POST.get("book_name", "").strip()
        season_name = request.POST.get("season_name", "").strip()
        lesson_name = request.POST.get("lesson_name", "").strip()
        subject_name = request.POST.get("subject_name", "").strip()

        course_obj, _ = Course.objects.get_or_create(name=course_name, designer=question_designer)

        book_obj, _ = Book.objects.get_or_create(name=book_name, course=course_obj)

        season_obj, _ = Season.objects.get_or_create(name=season_name, book=book_obj)

        lesson_obj, _ = Lesson.objects.get_or_create(name=lesson_name, season=season_obj)

        Subject.objects.create(name=subject_name, lesson=lesson_obj)

        return redirect('schoolview:designer_profile', request.user.id)

    context = {
        'courses': courses,
        'books': books,
        'seasons': seasons,
        'lessons': lessons,
        'subjects': subjects,
    }
    return render(request, 'forms/create_full_hierarchy.html', context)


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
            return redirect('schoolview:designer_questions', request.user.id)
    else:
        form = QuestionForm()
    return render(request, 'forms/create_question.html', {'form': form})


def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES, instance=question)
        if form.is_valid():
            form.save()
            return redirect('schoolview:designer_questions', request.user.id)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'forms/edit_question.html', {
        'form': form,
        'question': question
    })


def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    question.delete()
    return redirect('schoolview:designer_questions', request.user.id)


def designer_subquestions(request, designer_id):
    question_designer = get_object_or_404(Question_designer, designer_id=designer_id)
    subquestions = Subquestion.objects.filter(question_designer=question_designer)
    context = {
        'question_designer': question_designer,
        'subquestions': subquestions,
    }
    return render(request, 'school/designer_subquestions.html', context)


def edit_subquestion(request, subquestion_id):
    subquestion = get_object_or_404(Subquestion, id=subquestion_id)
    right_answers = Right_answer.objects.filter(subquestion=subquestion)
    wrong_answers = Wrong_answer.objects.filter(subquestion=subquestion)

    if request.method == "POST":
        subquestion_form = SubquestionForm(request.POST, request.FILES, instance=subquestion)
        right_answer_forms = [RightAnswerForm(request.POST, request.FILES, prefix=f"right-{answer.id}", instance=answer)
                              for answer in right_answers]
        wrong_answer_forms = [WrongAnswerForm(request.POST, request.FILES, prefix=f"wrong-{answer.id}", instance=answer)
                              for answer in wrong_answers]

        if subquestion_form.is_valid() and all(form.is_valid() for form in right_answer_forms + wrong_answer_forms):
            subquestion_form.save()
            for form in right_answer_forms + wrong_answer_forms:
                answer = form.save(commit=False)
                answer.subquestion = subquestion
                answer.save()
            return redirect('schoolview:designer_subquestions', request.user.id)
        else:
            raise ValueError

    else:
        subquestion_form = SubquestionForm(instance=subquestion)
        right_answer_forms = [RightAnswerForm(prefix=f"right-{answer.id}", instance=answer) for answer in right_answers]
        wrong_answer_forms = [WrongAnswerForm(prefix=f"wrong-{answer.id}", instance=answer) for answer in wrong_answers]

    return render(request, 'forms/edit_subquestion.html', {
        'subquestion_form': subquestion_form,
        'right_answer_forms': right_answer_forms,
        'wrong_answer_forms': wrong_answer_forms,
        'subquestion': subquestion
    })


def delete_subquestion(request, designer_id, subquestion_id):
    subquestion = get_object_or_404(Subquestion, id=subquestion_id)
    subquestion.delete()
    return redirect('schoolview:designer_subquestions', request.user.id)


def student_status_view(request, designer_id, student_id):
    student = get_object_or_404(Student, id=student_id)
    leitner = Leitner.objects.filter(student=student)
    exams = Practice.objects.filter(student=student)
    worksheets = Question_practice_worksheet.objects.filter(student=student).order_by('-date')
    practices = Practice.objects.filter(student=student)
    subquestions = Subquestion.objects.filter(practice__student=student).distinct()

    context = {
        'student': student,
        'leitner': leitner,
        'exams': exams,
        'worksheets': worksheets,
        'practices': practices,
        'subquestions': subquestions
    }
    return render(request, 'school/student_status.html', context)


def student_leitner_questions(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    subquestions = Subquestion.objects.all()
    leitner_questions = Leitner_question.objects.filter(student=student)
    question_status = []

    for subquestion in subquestions:
        if leitner_questions.filter(subquestion=subquestion).exists():
            status = True  # در لایتنر موجود هست
        else:
            status = False  # در لایتنر موجود نیست
        question_status.append({
            'text': subquestion.text,
            'status': status,
            'id': subquestion.id
        })

    context = {
        'student': student,
        'question_status': question_status,
    }

    return render(request, 'school/student_leitner_questions.html', context)


def add_to_leitner(request, student_id, subquestion_id):
    student = get_object_or_404(Student, id=student_id)
    subquestion = get_object_or_404(Subquestion, id=subquestion_id)
    if not Leitner_question.objects.filter(student=student, subquestion=subquestion).exists():
        Leitner_question.objects.create(student=student, subquestion=subquestion)
    else:
        return HttpResponse('this question is already in leitner')
    return redirect('schoolview:student_leitner_questions', student_id)


def remove_from_leitner(request, student_id, subquestion_id):
    student = get_object_or_404(Student, id=student_id)
    subquestion = get_object_or_404(Subquestion, id=subquestion_id)
    if Leitner_question.objects.filter(student=student, subquestion=subquestion).exists():
        Leitner_question.objects.filter(student=student, subquestion=subquestion).delete()
    else:
        return HttpResponse('this question is already removed')
    return redirect('schoolview:student_leitner_questions', student_id)


def subquestion_view(request, subquestion_id):
    subquestion = get_object_or_404(Subquestion, id=subquestion_id)
    return render(request, 'school/subquestion_view.html', {'subquestion': subquestion})
