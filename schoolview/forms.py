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
        fields = ['subquestion', 'title', 'image', 'audio_file', 'type']


class WrongAnswerForm(forms.ModelForm):
    class Meta:
        model = Wrong_answer
        fields = ['subquestion', 'title', 'image', 'audio_file', 'subject']


class SubquestionForm(forms.ModelForm):
    class Meta:
        model = Subquestion
        fields = ['text', 'image', 'score', 'time', 'course', 'book', 'season', 'lesson', 'subject']


RightAnswerFormSet = modelformset_factory(Right_answer, fields=('title', 'image', 'audio_file', 'type'), extra=1)
WrongAnswerFormSet = modelformset_factory(Wrong_answer, fields=('title', 'image', 'audio_file', 'subject'), extra=1)
