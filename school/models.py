from django.core.validators import FileExtensionValidator
from django.db import models
from account.models import Question_designer


# Create your models here.

def right_answer_upload_path(instance, filename):
    return f'right_answers/{instance.question.id}/{filename}'


def wrong_answer_upload_path(instance, filename):
    return f'wrong_answers/{instance.question.id}/{filename}'


class Education_stage(models.Model):
    desiner = models.ForeignKey(Question_designer, on_delete=models.CASCADE, related_name='education_stage')
    name = models.CharField(max_length=50)
    book = models.CharField(max_length=50, blank=True, null=True)
    season = models.CharField(max_length=50, blank=True, null=True)
    lesson = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'education_stage'
        ordering = ['-created_at']
        verbose_name = 'پایه تحصیلی(دوره)'


class Subject(models.Model):
    education_stage = models.ForeignKey(Education_stage, on_delete=models.CASCADE, related_name='subject')
    title = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'subject'
        ordering = ['-created_at']
        verbose_name = 'موضوع'


# social
class Social(models.Model):
    author = models.ForeignKey(Question_designer, on_delete=models.CASCADE, related_name='social')
    title = models.CharField(max_length=50)
    time = models.PositiveIntegerField(default=0)
    text = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='videos_uploaded/%Y/%m/%d/', null=True,blank=True,  validators=[
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


class Social_subject(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='social_subject')
    social = models.ForeignKey(Social, on_delete=models.CASCADE, related_name='social_subject')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} and {self.social}"

    class Meta:
        db_table = 'social_subject'
        ordering = ['-created_at']
        verbose_name = 'موضوع/رسانه'


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


class Subquestion(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='subquestion', blank=True, null=True)
    image = models.ImageField(upload_to='subquestion_images/%Y/%m/%d/', blank=True, null=True)
    text = models.TextField(blank=True, null=True)

    question_desiner = models.ForeignKey(Question_designer, on_delete=models.CASCADE, related_name='questions')
    education_stage = models.ManyToManyField(Education_stage, related_name='subquestion')
    score = models.PositiveIntegerField(default=0)
    time = models.TimeField(null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question}"

    class Meta:
        db_table = 'subquestion'
        ordering = ['-created_at']
        verbose_name = 'سوال'


class Right_answer(models.Model):
    TYPE_ANSWER = (
        ('-1', '-1'),
        ('0', '0'),
        ('n', 'n'),
    )
    question = models.ForeignKey(Subquestion, on_delete=models.CASCADE, related_name='right_answer')
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to=right_answer_upload_path, blank=True, null=True)
    audio_file = models.FileField(upload_to=right_answer_upload_path, blank=True, null=True)
    type = models.CharField(choices=TYPE_ANSWER, max_length=2, blank=False, null=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        db_table = 'right_answer'
        ordering = ['-created_at']


class Wrong_answer(models.Model):
    question = models.ForeignKey(Subquestion, on_delete=models.CASCADE, related_name='wrong_answer')
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
