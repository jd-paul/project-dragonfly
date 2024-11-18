from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from .models import UserType

def login_prohibited(view_function):
    """Decorator for view functions that redirect users away if they are logged in."""
    
    def modified_view_function(request):
        if request.user.is_authenticated:
            return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN)
        else:
            return view_function(request)
    return modified_view_function



def user_type_required(user_type):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.user_type == user_type:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return user_passes_test(lambda u: u.is_authenticated)(_wrapped_view)
    return decorator

admin_required = user_type_required(UserType.ADMIN)
tutor_required = user_type_required(UserType.TUTOR)
student_required = user_type_required(UserType.STUDENT)
