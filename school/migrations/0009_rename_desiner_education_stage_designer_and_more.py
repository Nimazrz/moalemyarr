# Generated by Django 5.1.5 on 2025-01-22 17:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0008_alter_education_stage_desiner'),
    ]

    operations = [
        migrations.RenameField(
            model_name='education_stage',
            old_name='desiner',
            new_name='designer',
        ),
        migrations.RenameField(
            model_name='subquestion',
            old_name='question_desiner',
            new_name='question_designer',
        ),
    ]
