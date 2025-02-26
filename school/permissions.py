from rest_framework import permissions


class IsQuestionDesigner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_question_designer


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_student
