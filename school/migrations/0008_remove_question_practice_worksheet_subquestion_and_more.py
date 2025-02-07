# Generated by Django 5.0.7 on 2025-02-07 08:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0007_rename_duration_subquestion_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question_practice_worksheet',
            name='subquestion',
        ),
        migrations.AlterField(
            model_name='question_practice_worksheet',
            name='date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='question_practice_worksheet',
            name='time_for_each_subquestion',
            field=models.DurationField(blank=True, default=datetime.timedelta(0), null=True),
        ),
        migrations.AlterField(
            model_name='question_practice_worksheet',
            name='time_spent',
            field=models.DurationField(blank=True, default=datetime.timedelta(0), null=True),
        ),
        migrations.AlterField(
            model_name='subquestion',
            name='time',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
