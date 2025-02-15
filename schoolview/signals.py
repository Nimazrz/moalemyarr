# from django.db.models.signals import pre_save, post_save
# from django.core.exceptions import ValidationError
# from django.dispatch import receiver
# from school.models import Leitner_question
#
#
# @receiver(pre_save, sender=Leitner_question)
# def update_leitner_question(sender, instance, **kwargs):
#     if instance.n == -1:
#         Leitner_question.objects.update(n=0)
#
