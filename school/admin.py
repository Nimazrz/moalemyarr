from django.contrib import admin

from account.models import Student
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


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Social)
class SocialAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'updated_at')
    inlines = [ImageInline]


@admin.register(Social_subject)
class SocialSubjectAdmin(admin.ModelAdmin):
    list_display = ('social',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(Subquestion)
class SubquestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'question_designer')
    inlines = [RightAnswerInline, WrongAnswerInline]


@admin.register(Practice)
class PracticeAdmin(admin.ModelAdmin):
    list_display = ('nf', 'nt')


@admin.register(Course_prerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ('prerequisite_course', 'course')


@admin.register(Study_report)
class StudyReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'social', 'time')


@admin.register(Question_practice_worksheet)
class QuestionPracticeWorksheetAdmin(admin.ModelAdmin):
    list_display = ('student', 'needed_time', 'time_spent')


@admin.register(Leitner_question)
class LeitnerQuestionAdmin(admin.ModelAdmin):
    list_display = ('student', 'subquestion', 'n')


@admin.register(Leitner)
class LeitnerAdmin(admin.ModelAdmin):
    list_display = ('student', 'last_step')
