# Generated by Django 5.0.7 on 2025-02-07 09:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0009_alter_question_practice_worksheet_time_for_each_subquestion_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question_practice_worksheet',
            old_name='time_for_each_subquestion',
            new_name='total_time',
        ),
    ]
