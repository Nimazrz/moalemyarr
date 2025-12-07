from rest_framework import permissions, status
from rest_framework.response import Response

class IsQuestionDesigner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_question_designer


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student
