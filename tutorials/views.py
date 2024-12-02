from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from django.utils.decorators import method_decorator
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TutorSignUpForm, StudentRequestForm
from tutorials.helpers import login_prohibited
from tutorials.models import UserType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator

from .models import User
from .models import UserType
from .models import StudentRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def dashboard(request):
    """Display the current user's dashboard."""
    user = request.user
    template_name = 'dashboard.html'
    return render(request, template_name, {'user': user})

@login_prohibited
def home(request):
    """Display the application's start/home screen."""
    return render(request, 'home.html')

class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url



class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)

class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


# Helper functions
def is_admin(user):
    if user.user_type == UserType.ADMIN:
        return True
    raise PermissionDenied

"""
Admin View Functions
"""
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class ManageTutors(View):
    """Display a list of pending tutor sign-up requests for admin approval."""
    template_name = 'admin/manage_tutors.html'
    paginate_by = 5

    def get_queryset(self):
        """Filter for tutors."""
        return User.objects.filter(user_type=UserType.TUTOR)

    def get(self, request, *args, **kwargs):
        """Display the list of tutors with pagination."""
        tutors_by_type = self.get_queryset()
        paginator = Paginator(tutors_by_type, self.paginate_by)
        page = request.GET.get('page', 1)

        try:
            tutors = paginator.page(page)
        except PageNotAnInteger:
            tutors = paginator.page(1)
        except EmptyPage:
            tutors = paginator.page(paginator.num_pages)

        tutor_count = tutors_by_type.count()

        context = {
            'tutors': tutors,
            'is_paginated': paginator.num_pages > 1,
            'tutor_count': tutor_count  # Pass the count to the template
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle approval or rejection of tutor sign-ups."""
        tutor_id = request.POST.get('tutor_id')
        action = request.POST.get('action')
        tutor = get_object_or_404(User, id=tutor_id, user_type=UserType.TUTOR)

        if action == 'approve':
            tutor.is_active = True
            tutor.save()
            messages.success(request, f"Tutor {tutor.get_full_name()} approved.")
        elif action == 'reject':
            tutor.delete()
            messages.success(request, "Tutor request rejected.")

        return redirect('manage_tutors')

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class ManageStudents(View):
    """Display a list of pending student sign-up requests for admin approval."""
    template_name = 'admin/manage_students.html'
    paginate_by = 15

    def get_queryset(self):
        """Retrieve the list of students."""
        return User.objects.filter(user_type=UserType.STUDENT)

    def get(self, request, *args, **kwargs):
        """Display the list of students with pagination."""
        students_by_type = self.get_queryset()
        paginator = Paginator(students_by_type, self.paginate_by)
        page = request.GET.get('page', 1)

        try:
            students = paginator.page(page)
        except PageNotAnInteger:
            students = paginator.page(1)
        except EmptyPage:
            students = paginator.page(paginator.num_pages)

        context = {
            'students': students,
            'is_paginated': paginator.num_pages > 1,
            'student_count': students_by_type.count()  # Pass the count to the template
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handle approval or rejection of student sign-ups."""
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')

        if not student_id or not action:
            messages.error(request, "Invalid action or student ID.")
            return redirect('manage_students')

        student = get_object_or_404(User, id=student_id, user_type=UserType.STUDENT)

        if action == 'approve':
            student.is_active = True
            student.save()
            messages.success(request, f"Student {student.get_full_name()} approved.")
        elif action == 'reject':
            student.delete()
            messages.success(request, "Student request rejected.")
        else:
            messages.error(request, "Invalid action provided.")

        return redirect('manage_students')

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class ManageApplications(View):
    """Display and manage pending student requests for admin approval."""
    template_name = 'admin/manage_applications.html'
    paginate_by = 15

    def get_queryset(self):
        """Retrieve the list of student requests."""
        return StudentRequest.objects.select_related('student', 'skill').order_by('-created_at')

    def get(self, request, *args, **kwargs):
        """Display the list of student requests with pagination."""
        requests = self.get_queryset()
        paginator = Paginator(requests, self.paginate_by)
        page = request.GET.get('page', 1)

        try:
            student_requests = paginator.page(page)
        except PageNotAnInteger:
            student_requests = paginator.page(1)
        except EmptyPage:
            student_requests = paginator.page(paginator.num_pages)

        context = {
            'student_requests': student_requests,
            'is_paginated': paginator.num_pages > 1,
            'request_count': requests.count()  # Total count of student requests
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handle approval or rejection of student requests."""
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        if not request_id or not action:
            messages.error(request, "Invalid action or request ID.")
            return redirect('manage_applications')

        student_request = get_object_or_404(StudentRequest, id=request_id)

        if action == 'approve':
            # Handle approval logic (customize as needed)
            student_request.student.is_active = True
            student_request.student.save()
            messages.success(request, f"Request for {student_request.student.get_full_name()} approved.")
        elif action == 'reject':
            # Handle rejection logic
            student_request.delete()
            messages.success(request, "Student request rejected.")
        else:
            messages.error(request, "Invalid action provided.")

        return redirect('manage_applications')

"""
Student View Functions
"""

# Student View

class RequestLesson(LoginRequiredMixin, FormView):
    """Display the requests screen and handle requests."""

    form_class = StudentRequestForm
    template_name = "request_lesson.html"
    login_url = 'login'  # Redirect to login page if not authenticated

    def get(self, request, *args, **kwargs):
        # Check if the logged-in user is a student
        if not (request.user.is_authenticated and request.user.user_type == 'Student'):
            return redirect('dashboard')  # Redirect non-student users to the dashboard
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Check if the logged-in user is a student
        if not (request.user.is_authenticated and request.user.user_type == 'Student'):
            return redirect('dashboard')  # Redirect non-student users to the dashboard
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)

class TutorSignUpView(LoginProhibitedMixin, FormView):
    """Display the tutor sign up screen and handle sign ups."""
    
    form_class = TutorSignUpForm
    template_name = "tutor_sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        # Save the user and set their type as TUTOR
        self.object = form.save()
        self.object.user_type = UserType.TUTOR
        self.object.save()
        
        # Optionally send a confirmation email or handle other tutor-specific logic
        
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tutor_dashboard')  # Redirect to tutor dashboard after successful signup
