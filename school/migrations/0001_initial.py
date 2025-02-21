# Generated by Django 5.0.7 on 2025-02-20 14:05

import datetime
import django.core.validators
import django.db.models.deletion
import school.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('audio_file', models.FileField(blank=True, null=True, upload_to='question_audios/%Y/%m/%d/')),
                ('image', models.ImageField(blank=True, null=True, upload_to='question_images/%Y/%m/%d/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'صورت سوال',
                'verbose_name_plural': 'صورت سوال',
                'db_table': 'question',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('designer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='account.question_designer')),
            ],
            options={
                'verbose_name': 'دوره ',
                'verbose_name_plural': 'دوره ها',
                'db_table': 'course',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='books', to='school.course')),
            ],
            options={
                'verbose_name': 'کتاب ',
                'verbose_name_plural': 'کتاب ها',
                'db_table': 'book',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Course_prerequisite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_prerequisits', to='school.course')),
                ('prerequisite_course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_prerequisite', to='school.course')),
            ],
            options={
                'verbose_name': 'پیش نیاز دوره',
                'verbose_name_plural': 'پیش نیاز های دوره',
                'db_table': 'course_prerequisite',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Leitner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_step', models.PositiveIntegerField(default=1)),
                ('datel', models.DateField(default=datetime.date(2025, 2, 19))),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leitner', to='account.student')),
            ],
            options={
                'verbose_name': 'لایتنر',
                'verbose_name_plural': 'لایتنر ها',
                'db_table': 'leitner',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Question_practice_worksheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_time', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('time_spent', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_practice_worksheet', to='account.student')),
            ],
            options={
                'verbose_name': 'کارنامه سوال تمرین',
                'verbose_name_plural': 'کارنامه های سوال،تمرین',
                'db_table': 'question_practice_worksheet',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seasons', to='school.book')),
            ],
            options={
                'verbose_name': 'فصل ',
                'verbose_name_plural': 'فصل ها',
                'db_table': 'season',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='school.season')),
            ],
            options={
                'verbose_name': 'درس ',
                'verbose_name_plural': 'درس ها',
                'db_table': 'lesson',
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
                ('video', models.FileField(blank=True, null=True, upload_to='videos_uploaded/%Y/%m/%d/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])])),
                ('view', models.PositiveIntegerField(default=0)),
                ('practical', models.BooleanField(default=False)),
                ('educational', models.BooleanField(default=False)),
                ('instance', models.BooleanField(default=False)),
                ('tip', models.BooleanField(default=False)),
                ('introduction', models.BooleanField(default=False)),
                ('summary', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social', to='account.question_designer')),
            ],
            options={
                'verbose_name': 'رسانه',
                'verbose_name_plural': 'رسانه',
                'db_table': 'social',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Study_report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('social', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='study_report', to='school.social')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='study_report', to='account.student')),
            ],
            options={
                'verbose_name': 'کارنامه مطالعه',
                'verbose_name_plural': 'کارنامه های مطالعاتی',
                'db_table': 'study_report',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='school.lesson')),
            ],
            options={
                'verbose_name': 'موضوع ',
                'verbose_name_plural': 'موضوع ها',
                'db_table': 'subject',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Social_subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('book', models.ManyToManyField(blank=True, related_name='social_subject', to='school.book')),
                ('course', models.ManyToManyField(blank=True, related_name='social_subject', to='school.course')),
                ('lesson', models.ManyToManyField(blank=True, related_name='social_subject', to='school.lesson')),
                ('season', models.ManyToManyField(blank=True, related_name='social_subject', to='school.season')),
                ('social', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_subject', to='school.social')),
                ('subject', models.ManyToManyField(blank=True, related_name='social_subject', to='school.subject')),
            ],
            options={
                'verbose_name_plural': 'موضوع/رسانه',
                'db_table': 'social_subject',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Subquestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='subquestion_images/%Y/%m/%d/')),
                ('text', models.TextField(blank=True, null=True)),
                ('score', models.PositiveIntegerField(default=0)),
                ('time', models.DurationField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('book', models.ManyToManyField(blank=True, related_name='subquestions', to='school.book')),
                ('course', models.ManyToManyField(blank=True, related_name='subquestions', to='school.course')),
                ('lesson', models.ManyToManyField(blank=True, related_name='subquestions', to='school.lesson')),
                ('question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subquestion', to='school.question')),
                ('question_designer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='account.question_designer')),
                ('season', models.ManyToManyField(blank=True, related_name='subquestions', to='school.season')),
                ('subject', models.ManyToManyField(blank=True, related_name='subquestions', to='school.subject')),
            ],
            options={
                'verbose_name': 'سوال',
                'verbose_name_plural': 'سوال ها',
                'db_table': 'subquestion',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Right_answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('image', models.ImageField(blank=True, null=True, upload_to=school.models.right_answer_upload_path)),
                ('audio_file', models.FileField(blank=True, null=True, upload_to=school.models.right_answer_upload_path)),
                ('type', models.CharField(choices=[('-1', '-1'), ('0', '0'), ('n', 'n')], max_length=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subquestion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='right_answer', to='school.subquestion')),
            ],
            options={
                'verbose_name_plural': 'جواب های درست',
                'db_table': 'right_answer',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Practice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zero', models.PositiveIntegerField(default=0)),
                ('nf', models.PositiveIntegerField(default=0)),
                ('nt', models.PositiveIntegerField(default=0)),
                ('date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ManyToManyField(to='account.student')),
                ('subquestion', models.ManyToManyField(to='school.subquestion')),
            ],
            options={
                'verbose_name': 'تمرین',
                'verbose_name_plural': 'تمرین ها',
                'db_table': 'practice',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Leitner_question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n', models.IntegerField(validators=[django.core.validators.MinValueValidator(-1), django.core.validators.MaxValueValidator(31)])),
                ('datelq', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leitner_question', to='account.student')),
                ('subquestion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leitner_question', to='school.subquestion')),
            ],
            options={
                'verbose_name_plural': 'لایتنر، سوال',
                'db_table': 'leitner_question',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Wrong_answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('image', models.ImageField(blank=True, null=True, upload_to=school.models.wrong_answer_upload_path)),
                ('audio_file', models.FileField(blank=True, null=True, upload_to=school.models.wrong_answer_upload_path)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wrong_answer', to='school.subject')),
                ('subquestion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wrong_answer', to='school.subquestion')),
            ],
            options={
                'verbose_name_plural': 'جواب های غلط',
                'db_table': 'wrong_answer',
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
