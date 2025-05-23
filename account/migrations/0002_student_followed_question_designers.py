# Generated by Django 5.1.6 on 2025-05-07 15:51

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='followed_question_designers',
            field=models.ManyToManyField(limit_choices_to={'is_question_designer': True}, related_name='followers_as_student', to=settings.AUTH_USER_MODEL),
        ),
    ]
