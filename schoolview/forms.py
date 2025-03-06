from django import forms
from account.models import CustomUser
from school.models import *
from django.forms import modelformset_factory, inlineformset_factory


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(max_length=20, widget=forms.PasswordInput, label='password')
    password2 = forms.CharField(max_length=20, widget=forms.PasswordInput, label='repeat password')

    class Meta:
        model = CustomUser
        fields = ['code_meli', 'username', 'first_name', 'last_name', 'is_question_designer', 'is_student']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('passwords doesnt match')
        return cd['password2']


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['code_meli', 'username', 'first_name', 'last_name', 'phone', 'email', 'address', 'province',
                  'city', 'county', 'landline_phone', 'bio', 'profile', 'is_question_designer', 'is_student']


class RightAnswerForm(forms.ModelForm):
    class Meta:
        model = Right_answer
        fields = ['title', 'image', 'audio_file', 'type']


class WrongAnswerForm(forms.ModelForm):
    class Meta:
        model = Wrong_answer
        fields = ['title', 'image', 'audio_file', 'subject']


RightAnswerFormSet = modelformset_factory(Right_answer, form=RightAnswerForm, extra=1, can_delete=True)
WrongAnswerFormSet = modelformset_factory(Wrong_answer, form=WrongAnswerForm, extra=1, can_delete=True)


class SubquestionForm(forms.ModelForm):
    class Meta:
        model = Subquestion
        fields = ['question', 'text', 'image', 'score', 'time', 'course', 'book', 'season', 'lesson', 'subject']

    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            return valid
        if not (self.cleaned_data.get('text') or self.cleaned_data.get('image')):
            raise forms.ValidationError('حداقل یکی از فیلدهای متن یا ایمج را پر کنید')
        return True


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name']


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['name']


class SeasonForm(forms.ModelForm):
    class Meta:
        model = Season
        fields = ['name']


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['name']


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'image', 'audio_file']