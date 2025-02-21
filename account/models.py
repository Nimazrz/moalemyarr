from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator


def image_directory_path(instance, filename):
    return f'photos/{instance.code_meli}/{instance.username}/{filename}'


class CustomUserManager(BaseUserManager):
    def _create_user(self, code_meli, password, is_staff=False, is_superuser=False, **other_fields):
        if not code_meli:
            raise ValidationError('فیلد کد ملی اجباری است')

        if not password:
            raise ValidationError('یک پسورد بسازی')

        user = self.model(
            code_meli=code_meli,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **other_fields
        )
        validate_password(password)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, code_meli, password, **other_fields):
        return self._create_user(code_meli, password, is_staff=False, is_superuser=False, **other_fields)

    def create_superuser(self, code_meli, password, **other_fields):
        return self._create_user(code_meli, password, is_staff=True, is_superuser=True, **other_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    # required
    code_meli = models.CharField(unique=True, max_length=10)
    username = models.CharField(unique=True, max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_question_designer = models.BooleanField(default=False, blank=False, null=False)
    is_student = models.BooleanField(default=False, blank=False, null=False)

    # optional
    phone = models.CharField(unique=True, max_length=11, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True, default=None)
    address = models.CharField(max_length=800, blank=True, null=True)
    province = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    county = models.CharField(max_length=50, blank=True, null=True)
    landline_phone = models.CharField(max_length=11, blank=True, null=True)
    bio = models.CharField(max_length=500, blank=True, null=True)
    profile = models.ImageField(upload_to=image_directory_path, blank=True, null=True)

    # settings
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'code_meli'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return f' {self.get_full_name()}'

    class Meta:
        db_table = 'custom_users'


class CommonFieldsMixin(models.Model):
    class Meta:
        abstract = True


class Admin(CommonFieldsMixin):
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin')

    class Meta:
        db_table = 'admin'


class Question_designer(CommonFieldsMixin):
    designer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='designer',
                                 limit_choices_to={'is_question_designer': True})

    def __str__(self):
        return f'Question_designer : {self.designer.username}(id:{self.designer.id})'

    class Meta:
        db_table = 'question_designer'


class Student(CommonFieldsMixin):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='student',
                                limit_choices_to={'is_student': True})

    def __str__(self):
        return f'Student : {self.student}'

    class Meta:
        db_table = 'student'
