from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from account.models import *
from school.models import *
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
import random


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

    def validate(self, data):
        password = data.get("password")
        password2 = data.pop("password2")
        if password != password2:
            raise serializers.ValidationError({"password": "passwords must match"})
        return data

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        user = CustomUser.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    code_meli = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        code_meli = data.get("code_meli")
        password = data.get("password")

        if not (code_meli or password):
            raise serializers.ValidationError("Both code_meli and password are required.")

        user = authenticate(code_meli=code_meli, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        data['user'] = user
        return data


class QuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'title', 'audio_file', 'image']

    def validate(self, attrs):
        if not any([attrs.get('title'), attrs.get('audio_file'), attrs.get('image')]):
            raise serializers.ValidationError(
                "At least one of 'title', 'audio_file', or 'image' must be provided."
            )
        return attrs


class RightanswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Right_answer
        fields = ['id', 'title', 'image', 'audio_file', 'type']


class WronganswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wrong_answer
        fields = ['id', 'title', 'image', 'audio_file', 'subject']


class SubquestionSerializer(serializers.ModelSerializer):
    right_answer = RightanswerSerializer(many=True, )
    wrong_answer = WronganswerSerializer(many=True, )

    class Meta:
        model = Subquestion
        fields = ['id', 'question_designer', 'question', 'image', 'text', 'score', 'time', 'course', 'book',
                  'season', 'lesson', 'subject', 'right_answer', 'wrong_answer']
        read_only_fields = ['question_designer']

    def validate(self, attrs):
        if 'right_answer' not in attrs or not attrs['right_answer']:
            raise serializers.ValidationError({"right_answer": "This field is required."})
        if 'wrong_answer' not in attrs or not attrs['wrong_answer']:
            raise serializers.ValidationError({"wrong_answer": "This field is required."})
        return attrs

    def create(self, validated_data):
        right_answers_data = validated_data.pop('right_answer', [])
        wrong_answers_data = validated_data.pop('wrong_answer', [])
        courses_data = validated_data.pop('course', [])
        books_data = validated_data.pop('book', [])
        seasons_data = validated_data.pop('season', [])
        lessons_data = validated_data.pop('lesson', [])
        subjects_data = validated_data.pop('subject', [])

        user = self.context['request'].user
        try:
            question_designer = Question_designer.objects.get(designer=user)
        except Question_designer.DoesNotExist:
            raise serializers.ValidationError("You are not authorized to create subquestions.")
        validated_data['question_designer'] = question_designer

        # Create the Subquestion instance
        subquestion = Subquestion.objects.create(**validated_data)

        subquestion.course.set(courses_data)  # Assuming IDs are provided
        subquestion.book.set(books_data)
        subquestion.season.set(seasons_data)
        subquestion.lesson.set(lessons_data)
        subquestion.subject.set(subjects_data)

        # Create related Right_answer instances
        for right_answer_data in right_answers_data:
            Right_answer.objects.create(subquestion=subquestion, **right_answer_data)

        # Create related Wrong_answer instances
        for wrong_answer_data in wrong_answers_data:
            Wrong_answer.objects.create(subquestion=subquestion, **wrong_answer_data)

        return subquestion


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"

    def validate(self, attrs):
        courses = Course.objects.filter(name__contains=attrs['name'])
        if courses.count() != 0:
            raise serializers.ValidationError({"course": "This course is already taken."})
        else:
            return attrs


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


class ExamSubquestionSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Subquestion
        fields = ['id', 'question_designer', 'question', 'image', 'text', 'score', 'time', 'answers']

    def get_answers(self, obj):
        # انتخاب یک جواب درست به صورت تصادفی
        right_answers = list(Right_answer.objects.filter(subquestion=obj))
        right_answer = random.choice(right_answers) if right_answers else None
        right_answer_data = RightanswerSerializer(right_answer).data if right_answer else None

        # انتخاب سه جواب غلط به صورت تصادفی
        wrong_answers = list(Wrong_answer.objects.filter(subquestion=obj))
        wrong_answers_selected = random.sample(wrong_answers, min(3, len(wrong_answers))) if wrong_answers else []
        wrong_answers_data = WronganswerSerializer(wrong_answers_selected,
                                                   many=True).data if wrong_answers_selected else []

        # ترکیب جواب درست و غلط در یک لیست
        answers_list = []
        if right_answer_data:
            answers_list.append(right_answer_data)
        answers_list.extend(wrong_answers_data)

        # ترکیب تصادفی جای جواب‌ها در لیست
        random.shuffle(answers_list)

        return answers_list


class LeitnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leitner
        fields = ["student", "last_step", "datel"]


class PracticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Practice
        fields = ["student", "subquestion", "zero", "nf", "nt", "date"]


class LeitnerQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leitner_question
        fields = ["student", "subquestion", "n", "datelq"]
        read_only_fields = ["student", "n", "datelq"]