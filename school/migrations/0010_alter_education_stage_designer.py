# Generated by Django 5.1.5 on 2025-01-23 19:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_remove_admin_user_remove_question_designer_user_and_more'),
        ('school', '0009_rename_desiner_education_stage_designer_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='education_stage',
            name='designer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='education_stage', to='account.question_designer'),
        ),
    ]
