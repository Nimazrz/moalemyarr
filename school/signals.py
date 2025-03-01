from django.db.models.signals import pre_save, post_save
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from .models import Subquestion
from account.models import CustomUser, Student, Question_designer
from django.conf import settings
from rest_framework.authtoken.models import Token

@receiver(pre_save, sender=Subquestion)
def validate_subquestion_fields(sender, instance, **kwargs):
    if not (instance.question or instance.image or instance.text):
        raise ValidationError("At least one of 'question', 'image', or 'text' must be provided.")


@receiver(post_save, sender=CustomUser)
def create_question_designer(sender, instance, created, **kwargs):
    if created and instance.is_question_designer:
        Question_designer.objects.create(designer=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)