from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import CustomUser, Admin, Question_designer, Student

@receiver(pre_save, sender=CustomUser)
def check_previous_status(sender, instance, **kwargs):
    """ قبل از ذخیره شدن یوزر، مقدار قبلی فیلدهای is_student و is_question_designer را ذخیره می‌کنیم """
    if instance.pk:  # اگر کاربر از قبل وجود داشته باشد
        previous_instance = CustomUser.objects.get(pk=instance.pk)
        instance._previous_is_student = previous_instance.is_student
        instance._previous_is_question_designer = previous_instance.is_question_designer
    else:
        instance._previous_is_student = False
        instance._previous_is_question_designer = False

@receiver(post_save, sender=CustomUser)
def create_or_delete_instance(sender, instance, created, **kwargs):
    """ هنگام ایجاد یا تغییر یوزر، مدل‌های مرتبط را ایجاد یا حذف می‌کنیم """

    if created:  # اگر کاربر تازه ایجاد شده باشد
        if instance.is_student:
            Student.objects.get_or_create(student=instance)
        if instance.is_superuser:
            Admin.objects.get_or_create(admin=instance)
        if instance.is_question_designer:
            Question_designer.objects.get_or_create(designer=instance)
    else:
        # حذف مدل دانش‌آموز اگر تیک دانش‌آموز برداشته شده باشد
        if instance._previous_is_student and not instance.is_student:
            Student.objects.filter(student=instance).delete()

        # ایجاد مدل دانش‌آموز اگر تیک دانش‌آموز اضافه شده باشد
        if not instance._previous_is_student and instance.is_student:
            Student.objects.get_or_create(student=instance)

        # حذف مدل طراح سوال اگر تیک طراح سوال برداشته شده باشد
        if instance._previous_is_question_designer and not instance.is_question_designer:
            Question_designer.objects.filter(designer=instance).delete()

        # ایجاد مدل طراح سوال اگر تیک طراح سوال اضافه شده باشد
        if not instance._previous_is_question_designer and instance.is_question_designer:
            Question_designer.objects.get_or_create(designer=instance)