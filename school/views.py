from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth import logout, login

from .serializer import *


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


class LoggoutAPIViwe(APIView):
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


class CreateQuestionAPIView(APIView):
    def post(self, request):
        serializer = CreateQuestionSerializer(data=request.data)  # Pass request.data to the serializer
        if serializer.is_valid():
            validated_data = serializer.validated_data
            Question.objects.create(
                title=validated_data.get("title"),
                audio_file=validated_data.get("audio_file"),
                image=validated_data.get("image")
            )
            return Response({"message": "Your question has been created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Include validation errors


class EducationStageAPIView(APIView):
    def post(self, request):
        serializer = EducationStageSerializer(data=request.data)
        if serializer.is_valid():
            if request.user.is_question_desiner:
                Education_stage.objects.create(
                    desiner=request.user,
                    name=serializer.validated_data.get("name"),
                    book=serializer.validated_data.get("book"),
                    season=serializer.validated_data.get("season"),
                    lesson=serializer.validated_data.get("lesson"),
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
