from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from account.models import *
from school.models import Question, Subquestion, Education_stage, Right_answer, Wrong_answer
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.core.exceptions import ObjectDoesNotExist


class SignupSerializer(serializers.Serializer):
    code_meli = serializers.CharField(max_length=10, min_length=10, required=True)
    username = serializers.CharField(max_length=50, min_length=2, required=True)
    first_name = serializers.CharField(max_length=50, min_length=2, required=True)
    last_name = serializers.CharField(max_length=50, min_length=2, required=True)
    is_question_designer = serializers.BooleanField(required=True)
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


class QuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id','title', 'audio_file', 'image']

    def validate(self, attrs):
        if not any([attrs.get('title'), attrs.get('audio_file'), attrs.get('image')]):
            raise serializers.ValidationError(
                "At least one of 'title', 'audio_file', or 'image' must be provided."
            )
        return attrs


class EducationStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education_stage
        fields = ['id','designer','name', 'book', 'season', 'lesson']
        read_only_fields = ['designer']

        def create(self, validated_data):
            user = self.context['request'].user
            try:
                # Get the Question_designer instance related to the logged-in user
                designer = Question_designer.objects.get(user=user)
            except ObjectDoesNotExist:
                raise serializers.ValidationError("You are not a valid question designer.")

            # Assign the question_designer to the validated_data
            validated_data['designer'] = designer

            # Create the Subquestion instance
            educationstage = super().create(validated_data)

        def update(self, instance, validated_data):
            # If you want to prevent modification of the designer field, we can handle it here
            validated_data.pop('designer', None)  # Remove designer from the update data to prevent overwriting

            # Update other fields
            return super().update(instance, validated_data)



class RightanswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Right_answer
        fields = ['id', 'title', 'image', 'audio_file', 'type']


class SubquestionSerializer(serializers.ModelSerializer):
    right_answers = RightanswerSerializer(many=True, write_only=True)

    class Meta:
        model = Subquestion
        fields = ['id', 'question_designer', 'question', 'image', 'text', 'education_stage', 'score', 'time',
                  'right_answers']
        read_only_fields = ['question_designer', ]

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            # Get the Question_designer instance related to the logged-in user
            question_designer = Question_designer.objects.get(user=user)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("You are not a valid question designer.")

        # Assign the question_designer to the validated_data
        validated_data['question_designer'] = question_designer

        # Create the Subquestion instance
        subquestion = super().create(validated_data)

        # Handle creating Right_answer instances
        right_answers_data = validated_data.pop('right_answers', [])
        for answer_data in right_answers_data:
            Right_answer.objects.create(subquestion=subquestion, **answer_data)

        return subquestion

        # def update(self, instance, validated_data):
        #     # Ensure the question_designer cannot be changed
        #     validated_data.pop('question_designer', None)
        #     return super().update(instance, validated_data)

