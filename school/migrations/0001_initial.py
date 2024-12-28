# Generated by Django 5.1.4 on 2024-12-19 23:46

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Education_stage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('book', models.CharField(blank=True, max_length=50, null=True)),
                ('season', models.CharField(blank=True, max_length=50, null=True)),
                ('lesson', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('desiner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='education_stage', to='account.question_designer')),
            ],
            options={
                'verbose_name': 'پایه تحصیلی(دوره)',
                'db_table': 'education_stage',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Social',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('time', models.PositiveIntegerField(default=0)),
                ('text', models.TextField(blank=True, null=True)),
                ('video', models.FileField(null=True, upload_to='videos_uploaded/%Y/%m/%d/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social', to='account.question_designer')),
            ],
            options={
                'verbose_name': 'رسانه',
                'db_table': 'social',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('education_stage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subject', to='school.education_stage')),
            ],
            options={
                'verbose_name': 'موضوع',
                'db_table': 'subject',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='social_subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('social', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_subject', to='school.social')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_subject', to='school.subject')),
            ],
            options={
                'verbose_name': 'موضوع/رسانه',
                'db_table': 'social_subject',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_file', models.ImageField(blank=True, null=True, upload_to='photos/%Y/%m/%d/')),
                ('title', models.CharField(blank=True, max_length=20, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('social', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='school.social')),
            ],
            options={
                'ordering': ['-created'],
                'indexes': [models.Index(fields=['-created'], name='school_imag_created_012d40_idx')],
            },
        ),
    ]
