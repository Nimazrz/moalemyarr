# Generated by Django 5.0.7 on 2025-01-21 21:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_rename_is_question_desiner_customuser_is_question_designer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='admin',
            name='user',
        ),
        migrations.RemoveField(
            model_name='question_designer',
            name='user',
        ),
        migrations.RemoveField(
            model_name='student',
            name='user',
        ),
    ]
