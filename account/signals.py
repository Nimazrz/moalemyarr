from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Admin, Question_designer, Student


@receiver(post_save, sender=CustomUser)
def create_instance(sender, instance, created, **kwargs):
    if created:  # Only run when a new user is created
        if instance.is_question_desiner:
            Question_designer.objects.create(designer=instance)
        elif instance.is_student:
            Student.objects.create(student=instance)
        elif instance.is_superuser:
            Admin.objects.create(admin=instance)
