from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TutorSignUpForm, StudentRequestForm
from tutorials.helpers import login_prohibited
from tutorials.models import User, UserType, Skill, SkillLevel, StudentRequest, PendingTutor, TutorSkill
from django.db.models import Q
from django.db.models import Case, When, Value, IntegerField

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

def is_student(user):
    if user.user_type == UserType.STUDENT:
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
    paginate_by = 15

    def get_queryset(self):
        """Filter for tutors."""
        return PendingTutor.objects.filter(is_approved=False)

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

        if not tutor_id or not action:
            messages.error(request, "Invalid request.")
            return redirect('manage_tutors')

        pending_tutor = get_object_or_404(PendingTutor, id=tutor_id)

        if action == 'approve':
            # Move data from PendingTutor to actual models
            user = pending_tutor.user
            user.user_type = UserType.TUTOR  # Ensure the user type is set to TUTOR
            user.is_active = True
            user.save()

            for skill in pending_tutor.skills.all():
                TutorSkill.objects.create(tutor=user, skill=skill, price_per_hour=pending_tutor.price_per_hour)

            pending_tutor.is_approved = True
            pending_tutor.save()
            messages.success(request, f"Tutor {user.get_full_name()} approved.")

        elif action == 'reject':
            # Reject the tutor by deleting the pending application
            pending_tutor.delete()
            messages.success(request, "Tutor request rejected.")

        else:
            messages.error(request, "Invalid action. Please try again.")

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

    def get_queryset(self, search_query=None, sort_by=None, order='asc'):
            """Retrieve the list of student requests, with optional search filtering."""
            requests = StudentRequest.objects.select_related('student', 'skill')

            if search_query:
                requests = requests.filter(
                    Q(student__first_name__icontains=search_query) |
                    Q(student__last_name__icontains=search_query)
                )

            # Sorting logic based on the selected sort field
            if sort_by == 'student':
                # Sort by student's full name (first_name or last_name)
                if order == 'asc':
                    requests = requests.order_by('student__first_name', 'student__last_name')
                else:
                    requests = requests.order_by('-student__first_name', '-student__last_name')
            elif sort_by == 'duration':
                # Sort by duration (numerically)
                if order == 'asc':
                    requests = requests.order_by('duration')
                else:
                    requests = requests.order_by('-duration')
            elif sort_by == 'created_at':
                # Sort by created_at (date)
                if order == 'asc':
                    requests = requests.order_by('created_at')
                else:
                    requests = requests.order_by('-created_at')
            elif sort_by == 'status':
                if order == 'asc_pending':
                    requests = requests.order_by(
                        Case(
                            When(status='pending', then=Value(1)),
                            When(status='approved', then=Value(2)),
                            When(status='rejected', then=Value(3)),
                            default=Value(4),
                            output_field=IntegerField()
                        )
                    )
                elif order == 'asc_accepted':
                    requests = requests.order_by(
                        Case(
                            When(status='approved', then=Value(1)),
                            When(status='pending', then=Value(2)),
                            When(status='rejected', then=Value(3)),
                            default=Value(4),
                            output_field=IntegerField()
                        )
                    )
                elif order == 'asc_rejected':
                    requests = requests.order_by(
                        Case(
                            When(status='rejected', then=Value(1)),
                            When(status='pending', then=Value(2)),
                            When(status='approved', then=Value(3)),
                            default=Value(4),
                            output_field=IntegerField()
                        )
                    )
                else:
                    requests = requests.order_by(
                        Case(
                            When(status='rejected', then=Value(1)),
                            When(status='approved', then=Value(2)),
                            When(status='pending', then=Value(3)),
                            default=Value(4),
                            output_field=IntegerField()
                        )
                    )

            return requests

    def get(self, request, *args, **kwargs):
        """Display the list of student requests with pagination."""
        search_query = request.GET.get('search', '')
        sort_by = request.GET.get('sort_by', 'created_at')
        order = request.GET.get('order', 'asc')

        requests = self.get_queryset(search_query, sort_by, order)

        # Calculate the total number of pending lessons
        pending_count = requests.filter(status='pending').count()

        paginator = Paginator(requests, self.paginate_by)
        page = request.GET.get('page', 1)

        try:
            student_requests = paginator.page(page)
        except PageNotAnInteger:
            student_requests = paginator.page(1)
        except EmptyPage:
            student_requests = paginator.page(paginator.num_pages)

        # Calculate the total number of lesson requests in the system
        total_lesson_requests = StudentRequest.objects.count()

        # Calculate the total number of approved lessons
        total_approved_lessons = StudentRequest.objects.filter(status='approved').count()

        context = {
            'student_requests': student_requests,
            'is_paginated': paginator.num_pages > 1,
            'request_count': requests.count(),  # Total count of student requests
            'pending_count': pending_count,  # Total count of pending lessons
            'total_lesson_requests': total_lesson_requests,  # Total count of lesson requests in the system
            'total_approved_lessons': total_approved_lessons,  # Total count of approved lessons
            'order': order,
            'search': search_query,
            'sort_by': sort_by,
        }
        return render(request, self.template_name, context)



@login_required
@user_passes_test(is_admin)
def LessonRequestDetails(request, id):
    """Display the details of a specific lesson request and allow tutor selection."""
    lesson_request = get_object_or_404(StudentRequest, id=id)  # Assuming StudentRequest represents a lesson request

    # Fetch tutors (example: all tutors, you can add filtering logic as needed)
    tutors = User.objects.filter(user_type=UserType.TUTOR)

    if 'assign_tutor' in request.GET:
        tutor_id = request.GET.get('assign_tutor')
        selected_tutor = get_object_or_404(User, id=tutor_id)
        lesson_request.tutor = selected_tutor  # Assign the selected tutor
        lesson_request.save()
        messages.success(request, f"Tutor {selected_tutor.get_full_name()} has been assigned.")
        return redirect('lesson_request_details', id=lesson_request.id)  # Redirect to refresh the page

    context = {
        'lesson_request': lesson_request,
        'tutors': tutors,
    }
    return render(request, 'admin/lesson_request_details.html', context)


@login_required
@user_passes_test(is_admin)
def update_request_status(request, request_id, action):
    """
    Update the status of a StudentRequest based on the action.
    Actions can be 'approve', 'reject', or 'pending'.
    """
    # Fetch the lesson request
    lesson_request = get_object_or_404(StudentRequest, id=request_id)

    # Determine the new status based on the action
    if action == 'approve':
        lesson_request.status = 'approved'
        messages.success(request, f"Request {lesson_request.id} has been approved.")
    elif action == 'reject':
        lesson_request.status = 'rejected'
        messages.success(request, f"Request {lesson_request.id} has been rejected.")
    elif action == 'pending':
        lesson_request.status = 'pending'
        messages.success(request, f"Request {lesson_request.id} has been set to pending.")
    else:
        messages.error(request, "Invalid action.")
        return redirect('manage_applications')

    # Save the updated status
    lesson_request.save()

    # Redirect to a relevant page
    return redirect('manage_applications')


"""
Student View Functions
"""

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class SkillListView(View):
    """Display a list of offered skills to student."""

    template_name = 'student/offered_skill_list.html'
    paginate_by = 10

    def get(self, request):
        query = request.GET.get('q', '')
        level = request.GET.get('level', '')
        skills = Skill.objects.all()

        if query:
            skills = skills.filter(language__icontains=query)
        if level:
            skills = skills.filter(level=level)

        paginator = Paginator(skills, self.paginate_by)
        page = request.GET.get('page', 1)

        try:
            skills_page = paginator.page(page)
        except PageNotAnInteger:
            skills_page = paginator.page(1)
        except EmptyPage:
            skills_page = paginator.page(paginator.num_pages)

        context = {
            'skills': skills_page,
            'query': query,
            'current_level': level,
            'levels': SkillLevel.choices,
            'is_paginated': paginator.num_pages > 1,
        }
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class RequestLesson(View):
    """Handle student's course request."""

    template_name = 'student/student_request_form.html'

    def get(self, request, skill_id):
        skill = get_object_or_404(Skill, id=skill_id)
        form = StudentRequestForm()
        return render(request, self.template_name, {'form': form, 'skill': skill})

    def post(self, request, skill_id):
        skill = get_object_or_404(Skill, id=skill_id)
        form = StudentRequestForm(request.POST)
        if form.is_valid():
            # Check if student has already requested the same course
            if StudentRequest.objects.filter(student=request.user, skill=skill).exists():
                messages.error(request, 'You have already requested this course.')
                return redirect('your_requests')
            
            student_request = form.save(commit=False)
            student_request.student = request.user
            student_request.skill = skill
            student_request.save()
            return redirect('your_requests')

        context = { 'skill': skill, 'form': form, }
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class YourRequestsView(View):
    template_name = 'student/your_requests.html'

    def get(self, request):
        
        student_requests = StudentRequest.objects.filter(student=request.user)
        for student_request in student_requests:
            student_request.is_accepted = student_request.enrollments.exists()
        context = {
            'student_requests': student_requests
        }
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class DeleteYourRequestView(View):
    def post(self, request, student_request_id):
        student_request = get_object_or_404(StudentRequest, id=student_request_id, student=request.user)
        if not student_request.enrollments.exists():
            student_request.delete()
            messages.success(request, 'Your request has been deleted.')
        else:
            messages.error(request, 'You cannot delete this request as it has been accepted already.')
        return redirect('your_requests')



class TutorSignUpView(LoginProhibitedMixin, FormView):
    form_class = TutorSignUpForm
    template_name = "tutor_sign_up.html"

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('tutor_application_success')

class TutorApplicationSuccessView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'tutor_application_success.html')
