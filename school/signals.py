from django.db.models.signals import pre_save
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from .models import Subquestion

@receiver(pre_save, sender=Subquestion)
def validate_subquestion_fields(sender, instance, **kwargs):
    if not (instance.question or instance.image or instance.text):
        raise ValidationError("At least one of 'question', 'image', or 'text' must be provided.")



