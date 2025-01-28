from django.shortcuts import render
from django.contrib.auth import logout, login
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.authentication import BasicAuthentication
from .serializer import *
from rest_framework.exceptions import PermissionDenied



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



