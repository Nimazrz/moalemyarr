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
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=11, min_length=11, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    province = serializers.CharField(required=False, allow_blank=True)
    county = serializers.CharField(required=False, allow_blank=True)
    landline_phone = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    profile_pic = serializers.ImageField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        password = data.get("password")
        password2 = data.pop("password2")
        if password != password2:
            raise serializers.ValidationError({"password": "passwords must match"})
        return data

    def validate_code_meli(self, value):
        if not value.isdigit() and len(value) == 10:
            raise serializers.ValidationError("کد ملی وارد شده صحیح نیست")
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(" کد ملی قبلا ثبت شده")
        return value

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("نام کاربری قبلاً ثبت شده است.")
        return value

    def validate_phone(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("شماره تلفن باید فقط شامل اعداد باشد")
        return value

    def validate_email(self, value):
        if value and CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return value

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        user = CustomUser.objects.create_user(**validated_data)
        return user


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

    def update(self, instance, validated_data):
        request = self.context['request']

        instance.text = request.data.get('text', instance.text)
        instance.score = request.data.get('score', instance.score)
        instance.time = request.data.get('time', instance.time)
        instance.question_id = request.data.get('question', instance.question_id)
        instance.save()

        if 'course' in validated_data:
            course_data = request.data.get('course')
            instance.course.set(course_data)
            instance.save()

        if 'book' in validated_data:
            book_data = request.data.get('book')
            instance.book.set(book_data)
            instance.save()

        if 'season' in validated_data:
            season_data = request.data.get('season')
            instance.season.set(season_data)
            instance.save()

        if 'lesson' in validated_data:
            lesson_data = request.data.get('lesson')
            instance.lesson.set(lesson_data)
            instance.save()

        if 'subject' in validated_data:
            subject_data = request.data.get('subject')
            instance.subject.set(subject_data)
            instance.save()

        right_answers_data = request.data.get('right_answer', [])
        right_answer_ids = []

        for answer_data in right_answers_data:
            answer_id = answer_data.get('id')
            if answer_id:
                try:
                    right_answer = Right_answer.objects.get(id=answer_id)
                    right_answer.title = answer_data['title']
                    right_answer.image = answer_data['image']
                    right_answer.audio_file = answer_data['audio_file']
                    right_answer.type = answer_data['type']
                    right_answer.save()
                    right_answer_ids.append(right_answer.id)
                except Right_answer.DoesNotExist:
                    pass
            else:
                new_answer = Right_answer.objects.create(subquestion=instance, **answer_data)
                right_answer_ids.append(new_answer.id)

        wrong_answers_data = request.data.get('wrong_answer', [])
        wrong_answer_ids = []

        for answer_data in wrong_answers_data:
            try:
                subject = Subject.objects.get(id=answer_data['subject'])
            except Subject.DoesNotExist:
                raise serializers.ValidationError({'subject': 'Invalid subject ID'})

            answer_id = answer_data.get('id')
            if answer_id:
                try:
                    wrong_answer = Wrong_answer.objects.get(id=answer_id)
                    wrong_answer.title = answer_data['title']
                    wrong_answer.image = answer_data['image']
                    wrong_answer.audio_file = answer_data['audio_file']
                    wrong_answer.subject = subject
                    wrong_answer.save()
                    wrong_answer_ids.append(wrong_answer.id)
                except Wrong_answer.DoesNotExist:
                    pass
            else:
                Wrong_answer.objects.create(
                    subquestion=instance,
                    title=answer_data['title'],
                    image=answer_data['image'],
                    audio_file=answer_data['audio_file'],
                    subject=subject
                )

        return instance

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

        subquestion = Subquestion.objects.create(**validated_data)

        subquestion.course.set(courses_data)
        subquestion.book.set(books_data)
        subquestion.season.set(seasons_data)
        subquestion.lesson.set(lessons_data)
        subquestion.subject.set(subjects_data)

        for right_answer_data in right_answers_data:
            Right_answer.objects.create(subquestion=subquestion, **right_answer_data)

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
    time = serializers.SerializerMethodField()

    class Meta:
        model = Subquestion
        fields = ['id', 'question_designer', 'question', 'image', 'text', 'score', 'time', 'answers']

    def get_time(self, obj):
        time_val = obj.time
        if hasattr(time_val, 'total_seconds'):
            total_seconds = int(time_val.total_seconds())
        elif isinstance(time_val, int):
            total_seconds = time_val
        else:
            return "00:00:00"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

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


class FollowUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'student', 'following']
        read_only_fields = ['id', 'student']

    def validate_following(self, value):
        if not CustomUser.objects.filter(id=value.id, is_question_designer=True).exists():
            raise serializers.ValidationError("کاربر انتخاب‌شده طراح سوال نیست.")
        return value


class ProfileSerializer(serializers.ModelSerializer):
    subquestions = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'profile', 'code_meli', 'username', 'first_name', 'last_name',
            'is_question_designer', 'is_student', 'phone', 'email', 'address',
            'province', 'city', 'county', 'landline_phone', 'bio',
            'questions', 'subquestions'
        ]
        read_only_fields = ['code_meli', 'username']

    def get_subquestions(self, user):
        if not user.is_question_designer:
            return None

        try:
            designer_obj = Question_designer.objects.get(designer=user)
        except Question_designer.DoesNotExist:
            return []

        subquestions = Subquestion.objects.filter(question_designer=designer_obj)
        return SubquestionSerializer(subquestions, many=True, context=self.context).data

    def get_questions(self, user):
        if not user.is_question_designer:
            return None
        questions = Question.objects.all()
        return QuestionsSerializer(questions, many=True, context=self.context).data
