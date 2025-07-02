from django.core.validators import FileExtensionValidator
from django.db import models
from account.models import Question_designer, CustomUser, Student
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date
# Create your models here.

def right_answer_upload_path(instance, filename):
    return f'right_answers/{instance.subquestion.id}/{filename}'


def wrong_answer_upload_path(instance, filename):
    return f'wrong_answers/{instance.subquestion.id}/{filename}'


class Course(models.Model):
    name = models.CharField(max_length=100)
    designer = models.ForeignKey(Question_designer, on_delete=models.CASCADE, related_name="courses")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f" پایه: {self.name}"

    class Meta:
        db_table = 'course'
        ordering = ['-created_at']
        verbose_name = 'دوره '
        verbose_name_plural = "دوره ها"


class Book(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="books")
    name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"کتاب:{self.name}, {self.course}"

    class Meta:
        db_table = 'book'
        ordering = ['-created_at']
        verbose_name = "کتاب "
        verbose_name_plural = "کتاب ها"


class Season(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="seasons")
    name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"فصل: {self.name}, {self.book}"

    class Meta:
        db_table = 'season'
        ordering = ['-created_at']
        verbose_name = "فصل "
        verbose_name_plural = "فصل ها"


class Lesson(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="lessons")
    name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f" درس:{self.name}, {self.season}"

    class Meta:
        db_table = 'lesson'
        ordering = ['-created_at']
        verbose_name = "درس "
        verbose_name_plural = "درس ها"


class Subject(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f" موضوع:{self.name}, {self.lesson}"

    class Meta:
        db_table = 'subject'
        ordering = ['-created_at']
        verbose_name = 'موضوع '
        verbose_name_plural = "موضوع ها"


# social
class Social(models.Model):
    author = models.ForeignKey(Question_designer, on_delete=models.CASCADE, related_name='social')
    title = models.CharField(max_length=50)
    time = models.PositiveIntegerField(default=0)
    text = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='videos_uploaded/%Y/%m/%d/', null=True, blank=True, validators=[
        FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])])
    view = models.PositiveIntegerField(default=0)

    practical = models.BooleanField(default=False)
    educational = models.BooleanField(default=False)
    instance = models.BooleanField(default=False)
    tip = models.BooleanField(default=False)
    introduction = models.BooleanField(default=False)
    summary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} by {self.author}'

    class Meta:
        db_table = 'social'
        ordering = ['-created_at']
        verbose_name = 'رسانه'
        verbose_name_plural = "رسانه"


class Social_subject(models.Model):
    social = models.ForeignKey(Social, on_delete=models.CASCADE, related_name='social_subject')

    course = models.ManyToManyField(Course, related_name='social_subject', blank=True)
    book = models.ManyToManyField(Book, related_name='social_subject', blank=True)
    season = models.ManyToManyField(Season, related_name='social_subject', blank=True)
    lesson = models.ManyToManyField(Lesson, related_name='social_subject', blank=True)
    subject = models.ManyToManyField(Subject, related_name='social_subject', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.social}"

    class Meta:
        db_table = 'social_subject'
        ordering = ['-created_at']
        verbose_name_plural = 'موضوع/رسانه'


class Image(models.Model):
    social = models.ForeignKey(Social, on_delete=models.CASCADE, related_name="images")
    image_file = models.ImageField(upload_to='photos/%Y/%m/%d/', blank=True, null=True)
    title = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created'])
        ]


# questions
class Question(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    audio_file = models.FileField(upload_to='question_audios/%Y/%m/%d/', blank=True, null=True)
    image = models.ImageField(upload_to='question_images/%Y/%m/%d/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        db_table = 'question'
        ordering = ['-created_at']
        verbose_name = 'صورت سوال'
        verbose_name_plural = "صورت سوال"


class Subquestion(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='subquestion', blank=True, null=True)
    image = models.ImageField(upload_to='subquestion_images/%Y/%m/%d/', blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    question_designer = models.ForeignKey(Question_designer, on_delete=models.CASCADE, related_name='questions')
    score = models.PositiveIntegerField(default=0)
    time = models.PositiveIntegerField(default=0)

    course = models.ManyToManyField(Course, related_name='subquestions', blank=True)
    book = models.ManyToManyField(Book, related_name='subquestions', blank=True, )
    season = models.ManyToManyField(Season, related_name='subquestions', blank=True)
    lesson = models.ManyToManyField(Lesson, related_name='subquestions', blank=True, )
    subject = models.ManyToManyField(Subject, related_name='subquestions', blank=True, )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.text}"

    class Meta:
        db_table = 'subquestion'
        ordering = ['-created_at']
        verbose_name = 'سوال'
        verbose_name_plural = "سوال ها"


class Right_answer(models.Model):
    TYPE_ANSWER = (
        ('-1', '-1'),
        ('0', '0'),
        ('n', 'n'),
    )
    subquestion = models.ForeignKey(Subquestion, on_delete=models.CASCADE, related_name='right_answer')
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to=right_answer_upload_path, blank=True, null=True)
    audio_file = models.FileField(upload_to=right_answer_upload_path, blank=True, null=True)
    type = models.CharField(choices=TYPE_ANSWER, max_length=2, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        db_table = 'right_answer'
        ordering = ['-created_at']
        verbose_name_plural = "جواب های درست"


class Wrong_answer(models.Model):
    subquestion = models.ForeignKey(Subquestion, on_delete=models.CASCADE, related_name='wrong_answer')
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to=wrong_answer_upload_path, blank=True, null=True)
    audio_file = models.FileField(upload_to=wrong_answer_upload_path, blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='wrong_answer', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        db_table = 'wrong_answer'
        ordering = ['-created_at']
        verbose_name_plural = "جواب های غلط"


class Practice(models.Model):
    student = models.ManyToManyField(Student)
    subquestion = models.ManyToManyField(Subquestion)
    zero = models.PositiveIntegerField(default=0)
    nf = models.PositiveIntegerField(default=0)
    nt = models.PositiveIntegerField(default=0)
    date = models.DateField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Practice, {', '.join([str(student) for student in self.student.all()])}"

    class Meta:
        db_table = 'practice'
        ordering = ['-created_at']
        verbose_name = 'تمرین'
        verbose_name_plural = "تمرین ها"


class Course_prerequisite(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_prerequisits')
    prerequisite_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_prerequisite')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.prerequisite_course.name} is a prerequisite for {self.course.name}"

    class Meta:
        db_table = 'course_prerequisite'
        ordering = ['-created_at']
        verbose_name = 'پیش نیاز دوره'
        verbose_name_plural = "پیش نیاز های دوره"


class Study_report(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='study_report')
    social = models.ForeignKey(Social, on_delete=models.CASCADE, related_name='study_report')
    time = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student}"

    class Meta:
        db_table = 'study_report'
        ordering = ['-created_at']
        verbose_name = 'کارنامه مطالعه'
        verbose_name_plural = "کارنامه های مطالعاتی"


class Question_practice_worksheet(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='question_practice_worksheet')
    total_time = models.PositiveIntegerField(default=0, blank=True, null=True)
    time_spent = models.PositiveIntegerField(default=0, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def exam_time(self):
        total_seconds = self.total_time
        return timedelta(seconds=total_seconds)

    def __str__(self):
        return f"{self.student}"

    class Meta:
        db_table = 'question_practice_worksheet'
        ordering = ['-created_at']
        verbose_name = 'کارنامه سوال تمرین'
        verbose_name_plural = "کارنامه های سوال،تمرین"


class Leitner_question(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leitner_question')
    subquestion = models.ForeignKey(Subquestion, on_delete=models.CASCADE, related_name='leitner_question')
    n = models.IntegerField(validators=[MinValueValidator(-1), MaxValueValidator(31)], default=0)
    datelq = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student}"

    class Meta:
        db_table = 'leitner_question'
        ordering = ['-created_at']
        verbose_name_plural = 'لایتنر، سوال'


class Leitner(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leitner')
    last_step = models.PositiveIntegerField(default=1)
    datel = models.DateField(default=timezone.now().date() - timezone.timedelta(days=1))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student}"

    class Meta:
        db_table = 'leitner'
        ordering = ['-created_at']
        verbose_name = 'لایتنر'
        verbose_name_plural = "لایتنر ها"
