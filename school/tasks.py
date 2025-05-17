# tasks.py
from celery import shared_task
from datetime import date
from .models import Subquestion, Right_answer, Practice, Question_practice_worksheet, Student
from django.contrib.auth import get_user_model


@shared_task
def process_exam_answers(user_id, user_answers, right_answers, subquestions_serializer):
    User = get_user_model()

    results = []
    total_time_seconds = 0

    student = Student.objects.filter(student__id=user_id).first()
    right_answers_dict = {}

    for answer in right_answers:
        sub_id = answer['subquestion_id']
        if sub_id not in right_answers_dict:
            right_answers_dict[sub_id] = []
        right_answers_dict[sub_id].append(answer['right_answer_id'])

    for sub_id_str, answer_id in user_answers.items():
        sub_id = int(sub_id_str)
        answer_id = int(answer_id)

        correct = right_answers_dict.get(sub_id, [])
        is_correct = answer_id in correct

        results.append({
            'subquestion_id': sub_id,
            'user_answer_id': answer_id,
            'correct_answer_id': correct[0] if correct else None,
            'is_correct': is_correct
        })

        practice = Practice.objects.filter(subquestion__id=sub_id).first()

        if not practice and student:
            subquestion = Subquestion.objects.get(id=sub_id)
            practice = Practice.objects.create(zero=0, nf=0, nt=0, date=date.today())
            practice.student.add(student)
            practice.subquestion.add(subquestion)

        if is_correct:
            practice.nt += 1
            practice.zero = 0
        else:
            practice.nf += 1
            practice.zero += 1

        practice.date = date.today()
        practice.save()

        for sub in subquestions_serializer:
            if sub['id'] == sub_id:
                time_value = sub.get('time')
                if isinstance(time_value, str):
                    try:
                        h, m, s = map(int, time_value.split(':'))
                        total_time_seconds += h * 3600 + m * 60 + s
                    except Exception:
                        pass
                elif isinstance(time_value, int):
                    total_time_seconds += time_value
                break

    if student:
        worksheet, _ = Question_practice_worksheet.objects.get_or_create(student=student, date=date.today())
        worksheet.time_spent += 20
        worksheet.total_time += total_time_seconds
        worksheet.save()

    return results