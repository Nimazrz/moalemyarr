from celery import shared_task
from datetime import date
from school.models import Subquestion, Right_answer, Practice, Question_practice_worksheet, Student
from django.contrib.auth import get_user_model

@shared_task
def process_worksheet(user_id, exam_data, questions_data, correct_answered):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    student = Student.objects.filter(student=user).first()
    if not student:
        return {"error": "Student not found"}

    for key, value in questions_data.items():
        subquestion = Subquestion.objects.get(id=value['subquestion_id'])
        correct_answers_from_db = set(
            Right_answer.objects.filter(subquestion=subquestion).values_list('title', flat=True))
        existing_practice = Practice.objects.filter(subquestion=subquestion).first()

        if not existing_practice:
            nt = nf = zero = 0
            if key in correct_answered and correct_answered[key]["user_answer"] in correct_answers_from_db:
                nt += 1
                zero = 0
            else:
                nf += 1
                zero += 1

            new_practice = Practice.objects.create(
                zero=zero, nf=nf, nt=nt, date=date.today()
            )
            new_practice.student.add(student)
            new_practice.subquestion.add(subquestion)
            new_practice.save()
        else:
            if key in correct_answered and correct_answered[key]["user_answer"] in correct_answers_from_db:
                existing_practice.nt += 1
                existing_practice.zero = 0
            else:
                existing_practice.nf += 1
                existing_practice.zero += 1
            existing_practice.date = date.today()
            existing_practice.save()

    worksheet, created = Question_practice_worksheet.objects.get_or_create(
        student=student, date=date.today(), defaults={"total_time": 0, "time_spent": 0}
    )
    worksheet.total_time += exam_data.get('total_time', 0)
    worksheet.time_spent += 20
    worksheet.save()
