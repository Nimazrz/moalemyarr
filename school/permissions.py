from rest_framework import permissions, status
from rest_framework.response import Response

class IsQuestionDesigner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_question_designer


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student


class SelfEditQuestionDesigner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            author = request.data.get('author')
            if request.user.is_authenticated:
                if request.user.id == author:
                    return True
                else:
                    return False
        else:
            return True
