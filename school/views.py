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
            return Response({"message" :"you have logged out succesfully"}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    

class CreateQuestionAPIView(APIView):
    def post(self, request):
        serializer = CreateQuestionSerializer(attrs=request.attrs)
        if serializer.is_valid():
            attrs = serializer.validated_data["attrs"]
            Question.objects.create(title=attrs["title"], audio_file=attrs["audio_file"], image=attrs["image"])
            return Response({"message" :"your question created"}, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
