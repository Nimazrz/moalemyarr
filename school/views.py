from django.contrib.auth import logout, login
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.authentication import BasicAuthentication
from .serializer import *
from rest_framework.exceptions import PermissionDenied
from datetime import date
import random
from django.shortcuts import get_object_or_404
from .models import *
from rest_framework.decorators import api_view, permission_classes
from django.db.models import F, ExpressionWrapper, IntegerField


# Create your views here.

class SignupAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    {
    "X-CSRFToken":"{% csrf_tocken %}"
    }
    """

    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
            return Response({"message": "you have logged out succesfully"}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionsSerializer
    # authentication_classes = (BasicAuthentication, IsAuthenticated)


class SubquestionViewSet(viewsets.ModelViewSet):
    queryset = Subquestion.objects.all()
    serializer_class = SubquestionSerializer
    authentication_classes = (BasicAuthentication,)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Subquestion.objects.all()
        elif hasattr(user, "is_question_designer") and user.is_question_designer:
            return Subquestion.objects.filter(question_designer__id=user.id)
        elif user.is_student:
            raise PermissionDenied("You are not allowed to view or submit questions.")

    def perform_create(self, serializer):
        user = self.request.user
        try:
            question_designer = Question_designer.objects.get(designer=user)
        except ObjectDoesNotExist:
            raise ValidationError("You are not a valid question designer.")

        serializer.save(question_designer=question_designer)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_exam(request: Request):
    student = Student.objects.filter(student=request.user).first()
    if request.method == "GET":
        # دریافت سوالات و محاسبه امتیاز
        subquestions = Subquestion.objects.annotate(
            total_calculation=ExpressionWrapper(
                (((F('practice__zero') * 2) - 1) * (F('practice__nf') + 1) / (F('practice__nt') + 1)),
                output_field=IntegerField())
        ).order_by('-total_calculation')

        # سریال‌سازی سوالات
        subquestions_serializer = ExamSubquestionSerializer(subquestions, many=True)
        subquestions_data = subquestions_serializer.data

        # استخراج جواب‌های درست از داده‌های سریال‌سازی‌شده
        # correct_answers = [
        #     {
        #         'subquestion_id': subquestion['id'],
        #         'correct_answer_id': next(
        #             (answer['id'] for answer in subquestion['answers'] if answer.get('type') is not None),
        #             None
        #         )
        #     }
        #     for subquestion in subquestions_data
        # ]
        # استخراج جواب‌های درست از دیتابیس
        right_answers = [
            {
                'subquestion_id': subquestion.id,
                'right_answer_id': correct_answer.id
            }
            for subquestion in subquestions
            for correct_answer in Right_answer.objects.filter(subquestion_id=subquestion.id, type__isnull=False)
        ]

        # ذخیره‌سازی داده‌ها در session
        request.session['subquestions_serializer'] = subquestions_data
        request.session['right_answers'] = right_answers

        return Response(subquestions_data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        # دریافت جواب‌های کاربر و جواب‌های درست از session
        user_answers = request.data.get('answers', {})
        right_answers = request.session.get('right_answers', [])

        # تبدیل right_answers به دیکشنری برای دسترسی سریع‌تر
        right_answers_dict = {}
        for answer in right_answers:
            subquestion_id = answer['subquestion_id']
            if subquestion_id not in right_answers_dict:
                right_answers_dict[subquestion_id] = []
            right_answers_dict[subquestion_id].append(answer['right_answer_id'])

        # بررسی جواب‌های کاربر
        results = []
        for subquestion_id, user_answer_id in user_answers.items():
            subquestion_id = int(subquestion_id)
            user_answer_id = int(user_answer_id)

            # دریافت جواب‌های درست برای سوال فعلی
            correct_answers_for_question = right_answers_dict.get(subquestion_id, [])
            is_correct = user_answer_id in correct_answers_for_question

            # ذخیره‌سازی نتیجه
            results.append({
                'subquestion_id': subquestion_id,
                'user_answer_id': user_answer_id,
                'correct_answer_id': correct_answers_for_question[0] if correct_answers_for_question else None,
                'is_correct': is_correct
            })

            practice = Practice.objects.filter(subquestion__id=subquestion_id).first()
            if not practice:
                if student:
                    subquestion = Subquestion.objects.get(id=subquestion_id)
                    practice = Practice.objects.create(
                        zero=0,
                        nf=0,
                        nt=0,
                        date=date.today()
                    )
                    practice.student.add(student)
                    practice.subquestion.add(subquestion)

            if is_correct:
                practice.nt += 1
                practice.zero = 0
                practice.date = date.today()
                practice.save()
                print(f"سوال {subquestion_id}: جواب کاربر درست است. انجام عملیات مربوطه...")
            else:
                practice.nf += 1
                practice.zero += 1
                practice.date = date.today()
                practice.save()
                print(f"سوال {subquestion_id}: جواب کاربر غلط است. انجام عملیات مربوطه...")

            # worksheet = Question_practice_worksheet.objects.get_or_create(
            #     student=student, date=date.today(), defaults={"total_time": 0, "time_spent": 0}
            # )
            #
            # worksheet.time_spent += 20
            # worksheet.save()

        return Response({"results": results}, status=status.HTTP_200_OK)






@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_worksheet(request):
    student = get_object_or_404(Student, student=request.user)
    exam_data = request.session.get('exam_data', {})
    questions_data = request.session.get('questions_data', {})
    correct_answered = request.session.get('correct_answered', {})

    for key, value in questions_data.items():
        subquestion = get_object_or_404(Subquestion, id=value['subquestion_id'])
        correct_answers_from_db = set(
            Right_answer.objects.filter(subquestion=subquestion).values_list('title', flat=True))
        existing_practice = Practice.objects.filter(subquestion=subquestion).first()

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
            except KeyError:
                existing_practice.nf += 1
                existing_practice.zero += 1
            existing_practice.date = date.today()
            existing_practice.save()

    worksheet, _ = Question_practice_worksheet.objects.get_or_create(
        student=student, date=date.today(), defaults={"total_time": 0, "time_spent": 0}
    )

    worksheet.total_time += exam_data.get('total_time', 0)
    worksheet.time_spent += 20
    worksheet.save()

    request.session.clear()
    return Response({"message": "Worksheet saved successfully!"}, status=status.HTTP_200_OK)
