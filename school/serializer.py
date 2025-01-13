from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from account.models import *
from school.models import Question
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login



class SignupSerializer(serializers.Serializer):
    code_meli = serializers.CharField(max_length=10, min_length=10, required=True)
    username = serializers.CharField(max_length=50, min_length=2, required=True)
    first_name = serializers.CharField(max_length=50, min_length=2, required=True)
    last_name = serializers.CharField(max_length=50, min_length=2, required=True)
    is_question_desiner = serializers.BooleanField(required=True)
    is_student = serializers.BooleanField(required=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=11, min_length=11, required=False)
    address = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    province = serializers.CharField(required=False)
    county = serializers.CharField(required=False)
    landline_phone = serializers.CharField(required=False)
    bio = serializers.CharField(required=False)
    profile_pic = serializers.ImageField(required=False)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def create(self, validated_data):
        password = validated_data.pop('password')
        password2 = validated_data.pop('password2')
        if password != password2:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        validated_data['password'] = make_password(password)
        user = CustomUser.objects.create(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    code_meli = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        code_meli = data.get("code_meli")
        password = data.get("password")

        if not code_meli or not password:
            raise serializers.ValidationError("Both code_meli and password are required.")

        user = authenticate(code_meli=code_meli, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        data['user'] = user
        return data

class CreateQuestionSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Question
        fields = ['title', 'audio_file', 'image']
    def validate(self, attrs):
        title = attrs.get("title")
        audio_file = attrs.get("audio_file")
        image = attrs.get("image")
        if not (title or audio_file or image):
            raise serializers.ValidationError("you shoud complete one of the fields")
        
        attrs["question"] = self.fields
        return attrs