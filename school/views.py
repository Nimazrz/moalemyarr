from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import BasicAuthentication
from .serializer import *
from .permissions import *
from django.shortcuts import get_object_or_404
from .models import *
from rest_framework.decorators import api_view, permission_classes
from django.db.models import F, ExpressionWrapper, IntegerField
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.db.models import Q
from .tasks import process_exam_answers
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from account.models import CustomUser


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'code_meli': user.code_meli,
            'username': user.username,

        })


class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckAuthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return JsonResponse({"user": {"username": request.user.username}})


class CSRFTokenView(APIView):
    def get(self, request):
        return JsonResponse({"csrfToken": get_token(request)})


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionsSerializer
    authentication_classes = (IsAuthenticated, )
    permissions_classes = (IsQuestionDesigner,)


class SubquestionViewSet(viewsets.ModelViewSet):
    queryset = Subquestion.objects.all()
    serializer_class = SubquestionSerializer
    permission_classes = [IsAuthenticated, IsQuestionDesigner]

    def get_queryset(self):
        custom_user = self.request.user
        question_designer = Question_designer.objects.filter(designer=custom_user).first()
        return Subquestion.objects.filter(question_designer=question_designer)


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


@permission_classes([IsAuthenticated])
@api_view(['GET', 'POST'])
def get_exam_filter(request: Request):
    if request.method == 'GET':
        return Response({
            'courses': CourseSerializer(Course.objects.all(), many=True).data,
            'books': BookSerializer(Book.objects.all(), many=True).data,
            'seasons': SeasonSerializer(Season.objects.all(), many=True).data,
            'lessons': LessonSerializer(Lesson.objects.all(), many=True).data,
            'subjects': SubjectSerializer(Subject.objects.all(), many=True).data,
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        course_ids = request.data.get('course_ids', [])
        book_ids = request.data.get('book_ids', [])
        season_ids = request.data.get('season_ids', [])
        lesson_ids = request.data.get('lesson_ids', [])
        subject_ids = request.data.get('subject_ids', [])

        courses = Course.objects.filter(id__in=course_ids)
        books = Book.objects.filter(id__in=book_ids)
        seasons = Season.objects.filter(id__in=season_ids)
        lessons = Lesson.objects.filter(id__in=lesson_ids)
        subjects = Subject.objects.filter(id__in=subject_ids)

        if len(courses) != len(course_ids):
            return Response({'error': 'Some courses not found'}, status=status.HTTP_400_BAD_REQUEST)
        if len(books) != len(book_ids):
            return Response({'error': 'Some books not found'}, status=status.HTTP_400_BAD_REQUEST)
        if len(seasons) != len(season_ids):
            return Response({'error': 'Some seasons not found'}, status=status.HTTP_400_BAD_REQUEST)
        if len(lessons) != len(lesson_ids):
            return Response({'error': 'Some lessons not found'}, status=status.HTTP_400_BAD_REQUEST)
        if len(subjects) != len(subject_ids):
            return Response({'error': 'Some subjects not found'}, status=status.HTTP_400_BAD_REQUEST)

        request._request.session['course_ids'] = course_ids
        request._request.session['book_ids'] = book_ids
        request._request.session['season_ids'] = season_ids
        request._request.session['lesson_ids'] = lesson_ids
        request._request.session['subject_ids'] = subject_ids

        return Response({
            'message': 'your categories selected'
        }, status=200)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_exam(request: Request):
    course_ids = request.session.get('course_ids', [])
    book_ids = request.session.get('book_ids', [])
    season_ids = request.session.get('season_ids', [])
    lesson_ids = request.session.get('lesson_ids', [])
    subject_ids = request.session.get('subject_ids', [])

    student = Student.objects.filter(student=request.user).first()
    if request.method == "GET":

        subquestions = Subquestion.objects.filter(
            Q(course__in=course_ids) |
            Q(book__in=book_ids) |
            Q(season__in=season_ids) |
            Q(lesson__in=lesson_ids) |
            Q(subject__in=subject_ids)
        ).annotate(
            total_calculation=ExpressionWrapper(
                (((F('practice__zero') * 2) - 1) * (F('practice__nf') + 1) / (F('practice__nt') + 1)),
                output_field=IntegerField())
        ).order_by('-total_calculation')
        subquestions_serializer = ExamSubquestionSerializer(subquestions, many=True)
        subquestions_data = subquestions_serializer.data

        right_answers = [
            {
                'subquestion_id': subquestion.id,
                'right_answer_id': correct_answer.id
            }
            for subquestion in subquestions
            for correct_answer in Right_answer.objects.filter(subquestion_id=subquestion.id, type__isnull=False)
        ]
        request.session['subquestions_serializer'] = subquestions_data
        request.session['right_answers'] = right_answers
        return Response(subquestions_data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        """
        {
         "answers":{
            "9":10,
            "11":12
        }}
        """
        user_answers = request.data.get('answers', {})
        right_answers = request.session.get('right_answers', [])
        subquestions_serializer = request.session.get('subquestions_serializer', {})
        task = process_exam_answers.delay(
            request.user.id,
            user_answers,
            right_answers,
            subquestions_serializer
        )
        return Response({"message": "Your answers are being processed."}, status=status.HTTP_202_ACCEPTED)


class LeitnerAPIView(APIView):
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
        student = get_object_or_404(Student, student=request.user)
        leitner, created = Leitner.objects.get_or_create(student=student)

        if leitner.last_step == 1 and leitner.datel == date.today():
            return Response({"message": "You have completed your Leitner for today"},
                            status=status.HTTP_400_BAD_REQUEST)

        numbers = (30, 14, 6, 2, 0)
        if leitner.last_step > 5:
            leitner.last_step = 1
            leitner.datel = date.today()
            self.upgrade_subquestions(student)
            leitner.save()
            return Response({"message": "Done for today"}, status=status.HTTP_200_OK)

        subquestions = Subquestion.objects.filter(leitner_question__n=numbers[(leitner.last_step) - 1])
        subquestions_serializer = ExamSubquestionSerializer(subquestions, many=True)
        subquestions_data = subquestions_serializer.data

        right_answers = [
            {
                'subquestion_id': subquestion.id,
                'right_answer_id': correct_answer.id
            }
            for subquestion in subquestions
            for correct_answer in Right_answer.objects.filter(subquestion_id=subquestion.id, type__isnull=False)
        ]

        if not subquestions_data:
            self.upgrade_subquestions(student)
            leitner.last_step += 1
            leitner.datel = date.today()
            leitner.save()
            return Response({"message": "No subquestions for this step, go for rest of them"},
                            status=status.HTTP_200_OK)

        request.session['right_answers'] = right_answers
        return Response(
            {'subquestions_data': subquestions_data,
             'last_step': leitner.last_step},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        """
            {
              "answers": [
                {"question_id": 1, "answer_id": 7},
                {"question_id": 9, "answer_id": 9}
              ]
            }
        """
        student = get_object_or_404(Student, student=request.user)
        right_answers = request.session.get("right_answers", [])
        print(right_answers)

        user_answers_list = request.data.get("answers", [])
        user_answers = {str(item["question_id"]): item["answer_id"] for item in user_answers_list}
        right_answers_dict = {}
        for answer in right_answers:
            print("halge")
            subquestion_id = answer['subquestion_id']
            if subquestion_id not in right_answers_dict:
                right_answers_dict[subquestion_id] = []
            right_answers_dict[subquestion_id].append(answer['right_answer_id'])
        results = []
        leitner = Leitner.objects.filter(student=student).first()
        for subquestion_id, user_answer_id in user_answers.items():
            print("for loop")
            subquestion_id = int(subquestion_id)
            user_answer_id = int(user_answer_id)

            correct_answers_for_question = right_answers_dict.get(subquestion_id, [])
            is_correct = user_answer_id in correct_answers_for_question

            results.append({
                'subquestion_id': subquestion_id,
                'user_answer_id': user_answer_id,
                'correct_answer_id': correct_answers_for_question[0] if correct_answers_for_question else None,
                'is_correct': is_correct
            })

            leitner_question = Leitner_question.objects.get(subquestion_id=subquestion_id)

            practice = Practice.objects.filter(subquestion__id=subquestion_id).first()
            print("in para")
            if not practice:
                print("practice")
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
                print("correct")
                leitner.last_step += 1
                leitner.datel = date.today()
                leitner.save()

                leitner_question.n += 1
                leitner_question.datelq = date.today()
                leitner_question.save()

                practice.nt += 1
                practice.zero = 0
                practice.date = date.today()
                practice.save()
            else:
                print("incorrect")
                leitner.last_step += 1
                leitner.datel = date.today()
                leitner.save()

                leitner_question.n = -1
                leitner_question.datelq = date.today()
                leitner_question.save()

                practice.nf += 1
                practice.zero += 1
                practice.date = date.today()
                practice.save()
        print(results)
        self.upgrade_subquestions(student)

        return Response({'results': results}, status=status.HTTP_200_OK)


class LeitnerQuestionViewSet(viewsets.ModelViewSet):
    queryset = Leitner_question.objects.all()
    serializer_class = LeitnerQuestionSerializer
    authentication_classes = (BasicAuthentication,)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        student = get_object_or_404(Student, student=self.request.user)
        return Leitner_question.objects.filter(student=student)

    def create(self, request, *args, **kwargs):
        custom_user = get_object_or_404(CustomUser, id=self.request.user.id)
        if not custom_user.is_student:
            return Response({"message": "You are not allowed to create questions"}, )
        student = get_object_or_404(Student, student=custom_user)
        subquestion_id = request.data['subquestion']
        if Leitner_question.objects.filter(student=student, subquestion_id=subquestion_id).exists():
            return Response({"message": "Subquestion already exists"}, status=status.HTTP_400_BAD_REQUEST)
        Leitner_question.objects.create(student=student, subquestion_id=subquestion_id)
        return Response({"message": "Leitner question created"}, status=status.HTTP_201_CREATED)


class FollowQuestionDesignerView(APIView):
    def post(self, request):
        user = request.user
        student_instance = get_object_or_404(Student, student=user)

        try:
            designer_id = int(request.data.get('following'))
        except (TypeError, ValueError):
            return Response({'error': 'شناسه طراح سوال نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)

        designer_user = get_object_or_404(CustomUser, id=designer_id, is_question_designer=True)

        student_instance.following.add(designer_user)

        return Response({'message': 'طراح سوال با موفقیت دنبال شد.'}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user
