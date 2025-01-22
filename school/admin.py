from django.contrib import admin
from .models import *


# Register your models here.


class ImageInline(admin.TabularInline):
    model = Image
    extra = 0


class RightAnswerInline(admin.TabularInline):
    model = Right_answer
    extra = 0


class WrongAnswerInline(admin.TabularInline):
    model = Wrong_answer
    extra = 0


@admin.register(Education_stage)
class EducationStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'book', 'designer')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'education_stage')


@admin.register(Social)
class SocialAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'updated_at')
    inlines = [ImageInline]


@admin.register(Social_subject)
class SocialSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'social')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', )


@admin.register(Subquestion)
class SubquestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'question_designer')
    inlines = [RightAnswerInline, WrongAnswerInline]