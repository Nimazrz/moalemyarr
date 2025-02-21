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
    if request.method == "GET":
        subquestions = Subquestion.objects.annotate(
            total_calculation=ExpressionWrapper(
                (((F('practice__zero') * 2) - 1) * (F('practice__nf') + 1) / (F('practice__nt') + 1)),
                output_field=IntegerField())
        ).order_by('-total_calculation')

        subquestions_serializer = ExamSubquestionSerializer(subquestions, many=True)
        request.session['subquestions_serializer'] = subquestions_serializer.data
        return Response(subquestions_serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":

        user_answers = {key: request.data.get(key) for key in request.session.get('correct_answers', {})}
        request.session['user_answers'] = user_answers
        return Response({"message": "Answers submitted successfully"}, status=status.HTTP_200_OK)


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
