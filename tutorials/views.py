from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from tutorials.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TutorSignUpForm, StudentRequestForm, TicketForm
from tutorials.helpers import login_prohibited
from tutorials.models import User, UserType, Skill, SkillLevel, StudentRequest, PendingTutor, TutorSkill, Enrollment, Ticket, TicketStatus, Invoice
from django.db.models import Q
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Prefetch
from datetime import timedelta
from django.http import HttpResponseNotFound

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

def is_tutor(user):
    if user.user_type == UserType.TUTOR:
        return True
    raise PermissionDenied

class PaginatorMixin:
    """A Mixin for adding pagination."""
    paginate_by = 10

    def paginator_queryset(self, request, queryset):
        """Paginate the queryset."""
        page = request.GET.get('page', 1)
        paginator = Paginator(queryset, self.paginate_by)
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)
        return items


    def get_paginated_context(self, items, object_name):
        """Prepare the context data for the template with pagination details."""
        return {
            'is_paginated': items.has_other_pages(),
            object_name: items
        }


"""
Admin View Functions
"""

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class ManageTutors(PaginatorMixin, View):
    """Display a list of pending tutor sign-up requests for admin approval."""
    template_name = 'admin/manage_tutors.html'

    def get_queryset(self):
        """Filter for pending tutors and order by ID."""
        return PendingTutor.objects.filter(is_approved=False).order_by('id')


    def get_current_tutors(self):
        """Retrieve approved tutors."""
        # return User.objects.filter(user_type=UserType.TUTOR, is_active=True)
        """Retrieve all active tutors along with their skills."""
        return User.objects.filter(
            user_type=UserType.TUTOR, 
            is_active=True
        ).prefetch_related(
            Prefetch(
                'skills',  # This matches the related_name on the TutorSkill model
                queryset=TutorSkill.objects.select_related('skill')
            )
        )
    def get(self, request, *args, **kwargs):
        """Display the list of tutors with pagination."""
        # Pending tutors
        pending_tutors = self.get_queryset()
        pending_paginator = Paginator(pending_tutors, self.paginate_by)
        page = request.GET.get('page', 1)

        try:
            tutors = pending_paginator.page(page)
        except PageNotAnInteger:
            tutors = pending_paginator.page(1)
        except EmptyPage:
            tutors = pending_paginator.page(pending_paginator.num_pages)

        pending_count = pending_tutors.count()

        # Approved tutors
        current_tutors = self.get_current_tutors()
        current_tutors_count = current_tutors.count()

        context = {
            'tutors': tutors,
            'is_paginated': pending_paginator.num_pages > 1,
            'tutor_count': pending_count,
            'current_tutors': current_tutors,  # Pass current tutors to the template
            'current_tutors_count': current_tutors_count  # Count of approved tutors
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
class ManageStudents(PaginatorMixin, View):
    """Display a list of pending student sign-up requests for admin approval."""
    template_name = 'admin/manage_students.html'


    def get_queryset(self):
        """Retrieve the list of students."""
        return User.objects.filter(user_type=UserType.STUDENT)


    def get(self, request, *args, **kwargs):
        """Display the list of students with pagination."""
        students_by_type = self.get_queryset()
        paginated_students = self.paginator_queryset(request, students_by_type)
        context = self.get_paginated_context(paginated_students, 'students')
        context['student_count'] = students_by_type.count()
        return render(request, self.template_name, context)

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
                elif order == 'asc_approved':
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

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class ManageLessons(View):
    """
    Admin view for managing lessons.
    """
    template_name = 'admin/manage_lessons.html'
    paginate_by = 10  # or whatever number you want per page

    def get_queryset(self, search_query=None, status_filter=None):
        """
        Retrieve all lessons with optional search and status filters.
        """
        lessons = Enrollment.objects.select_related('approved_request__student', 'tutor', 'approved_request__skill')

        if search_query:
            lessons = lessons.filter(
                Q(approved_request__student__first_name__icontains=search_query) |
                Q(approved_request__student__last_name__icontains=search_query) |
                Q(tutor__first_name__icontains=search_query) |
                Q(tutor__last_name__icontains=search_query) |
                Q(approved_request__skill__language__icontains=search_query)
            )

        if status_filter:
            lessons = lessons.filter(status=status_filter)

        # Add explicit ordering
        return lessons.order_by('-created_at')  # Adjust ordering field as needed


    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to display lessons with pagination,
        similar to ManageApplications logic.
        """
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        lessons = self.get_queryset(search_query, status_filter)

        # Set up pagination
        paginator = Paginator(lessons, self.paginate_by) # There might be an error here! Look at this mr GPT
        page = request.GET.get('page', 1)

        try:
            student_lessons = paginator.page(page)
        except PageNotAnInteger:
            student_lessons = paginator.page(1)
        except EmptyPage:
            student_lessons = paginator.page(paginator.num_pages)

        # Add any counts or additional context if needed
        ongoing_count = Enrollment.objects.filter(status='ongoing').count()
        cancelled_count = Enrollment.objects.filter(status='cancelled').count()

        context = {
            'lessons': student_lessons,
            'is_paginated': paginator.num_pages > 1,
            'search_query': search_query,
            'status_filter': status_filter,
            'ongoing_count': ongoing_count,
            'cancelled_count': cancelled_count,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to update lesson status.
        """
        lesson_id = request.POST.get('lesson_id')
        action = request.POST.get('action')

        lesson = get_object_or_404(Enrollment, id=lesson_id)

        if action == 'cancel' and lesson.status == 'ongoing':
            lesson.status = 'cancelled'
            lesson.save()
            messages.success(request, f"Lesson {lesson.id} has been marked as cancelled.")
        else:
            messages.error(request, "Invalid action or lesson status.")

        return redirect('manage_lessons')

@login_required
@user_passes_test(is_admin)
def LessonRequestDetails(request, id):
    """Display the details of a specific lesson request and handle tutor assignment."""
    lesson_request = get_object_or_404(StudentRequest, id=id)

    # Fetch tutors with requested skill
    skill_needed = lesson_request.skill
    tutors = User.objects.filter(user_type=UserType.TUTOR, skills__skill=skill_needed).distinct()

    # Pre-fetch related TutorSkills to reduce query count
    tutors_with_skills = []
    for tutor in tutors:
        tutor_skills = TutorSkill.objects.filter(tutor=tutor)
        tutors_with_skills.append({
            'tutor': tutor,
            'skills': tutor_skills
        })

    # Handle tutor assignment
    if 'assign_tutor' in request.GET:
        tutor_id = request.GET.get('assign_tutor')
        selected_tutor = get_object_or_404(User, id=tutor_id, user_type=UserType.TUTOR)

        # Modify existing enrollment or create a new one
        enrollment, created = Enrollment.objects.get_or_create(
            approved_request=lesson_request,
            defaults={
                'current_term': lesson_request.first_term,
                'tutor': selected_tutor,
                'week_count': 12,
                'start_time': timezone.now() + timedelta(days=2),
                'status': 'ongoing',
            },
        )

        if not created:
            enrollment.tutor = selected_tutor
            enrollment.start_time = timezone.now() + timedelta(days=2)
            enrollment.save()
            messages.success(request, f"Tutor updated to {selected_tutor.get_full_name()}.")
        else:
            Invoice.objects.create(
                enrollment=enrollment,
                amount=0.00,
                issued_date=timezone.now(),
                payment_status='unpaid',
                due_date=enrollment.start_time,
            )
            messages.success(request, f"Tutor {selected_tutor.get_full_name()} assigned and enrollment created.")
        return redirect('lesson_request_details', id=lesson_request.id)

    # Get the latest Enrollment associated with this StudentRequest, if any
    latest_enrollment = lesson_request.enrollments.order_by('-created_at').first()

    # Ensure the function always renders a response
    context = {
        'lesson_request': lesson_request,
        'tutors_with_skills': tutors_with_skills,
        'latest_enrollment': latest_enrollment,
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

        lesson_request.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'manage_applications'))
    elif action == 'pending':
        lesson_request.status = 'pending'
        messages.success(request, f"Request {lesson_request.id} has been set to pending.")

        lesson_request.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'manage_applications'))
    else:
        messages.error(request, "Invalid action.")
        return redirect('manage_applications')

    # Save the updated status
    lesson_request.save()

    # Redirect to a relevant page
    return redirect('manage_applications')

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class ManageTickets(View):
    """Manage tickets submitted by users."""

    template_name = 'admin/manage_tickets.html'

    def get_queryset(self):
        """Retrieve all tickets."""
        return Ticket.objects.all().order_by('-created_at')

    def get(self, request, *args, **kwargs):
        """Display the list of tickets with pagination."""
        tickets = self.get_queryset()

        # Categorise tickets
        new_tickets = tickets.filter(status=TicketStatus.PENDING)
        resolved_tickets = tickets.filter(status__in=[TicketStatus.APPROVED, TicketStatus.REJECTED])

        context = {
            'new_tickets': new_tickets,
            'resolved_tickets': resolved_tickets,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle ticket updates (e.g., change status)."""
        ticket_id = request.POST.get('ticket_id')
        action = request.POST.get('action')

        if not ticket_id or not action:
            messages.error(request, "Invalid request.")
            return redirect('manage_tickets')

        ticket = get_object_or_404(Ticket, id=ticket_id)

        if action == 'approve':
            ticket.status = TicketStatus.APPROVED
            ticket.save()
            messages.success(request, f"Ticket '{ticket.id}' has been approved.")
        elif action == 'reject':
            ticket.status = TicketStatus.REJECTED
            ticket.save()
            messages.success(request, f"Ticket '{ticket.id}' has been rejected.")
        else:
            messages.error(request, "Invalid action. Please try again.")

        return redirect('manage_tickets')

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class InvoiceView(View):
    """Display invoice to student"""
    template_name = 'student/invoice.html'


    def get(self, request, enrollment_id):
        """Display the invoice details for a student."""
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        if enrollment.approved_request.student != request.user:
            raise PermissionDenied("You do not have permission to view this invoice.")
        try:
            invoice = enrollment.invoice
        except Invoice.DoesNotExist:
            return HttpResponseNotFound("Invoice does not exist for this enrollment.")


        context = {
            'student': enrollment.approved_request.student,
            'tutor': enrollment.tutor,
            'start_time': enrollment.start_time,
            'term': enrollment.current_term,
            'frequency': enrollment.approved_request.frequency,
            'amount': invoice.subtotal,
            'tutor_skill': enrollment.tutor.skills.get(skill=enrollment.approved_request.skill).skill
        }
        return render(request, self.template_name, context)

"""
Student View Functions
"""

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class SkillListView(PaginatorMixin, View):
    """Display a list of offered skills to student."""
    template_name = 'student/offered_skill_list.html'


    def get_queryset(self, request):
        """Retrieve and filter the list of skills based on query parameters."""
        query = request.GET.get('q', '')
        level = request.GET.get('level', '')
        skills = Skill.objects.all()


        if query:
            skills = skills.filter(language__icontains=query)
        if level:
            skills = skills.filter(level=level)
        
        return skills


    def get(self, request):
        """Display the list of skills with pagination and filtering."""
        skills = self.get_queryset(request)
        paginated_skills = self.paginator_queryset(request, skills)
        context = self.get_paginated_context(paginated_skills, 'skills')
        context['query'] = request.GET.get('q', '')
        context['current_level'] =  request.GET.get('level', '')
        context['levels'] =  SkillLevel.choices

        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class RequestLesson(View):
  """Handle student requesting a course."""

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
        context = {
            'student_requests': student_requests
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class DeleteYourRequestView(View):
    def post(self, request, student_request_id):
        student_request = get_object_or_404(StudentRequest, id=student_request_id, student=request.user)
        if  student_request.status == 'pending':
            student_request.delete()
            messages.success(request, 'Your request has been deleted.')
        else:
            messages.error(request, 'You cannot delete this request.')
        return redirect('your_requests')


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_student), name='dispatch')
class YourEnrollmentsView(View):
    template_name = 'student/your_enrollments.html'

    def get(self, request):
        approved_requests = StudentRequest.objects.filter(student=request.user, status='approved')
        enrollments = Enrollment.objects.filter(approved_request__in=approved_requests)
        for enrollment in enrollments:
            enrollment.has_invoice = Invoice.objects.filter(enrollment=enrollment).exists()
        context = {
            'enrollments': enrollments
        }

        return render(request, self.template_name, context)

class TutorSignUpView(LoginProhibitedMixin, FormView):
    form_class = TutorSignUpForm
    template_name = "tutor_sign_up.html"
    redirect_when_logged_in_url = 'dashboard'  

    def form_valid(self, form):
        user = form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Your application to become a tutor has been submitted! We will review your application and get back to you soon.")
        return reverse('home')

class TutorApplicationSuccessView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'tutor_application_success.html', {
            'home_url': 'http://localhost:8000/'  # This will be the URL for the homepage
        })

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_tutor), name='dispatch')
class TutorEnrollmentList(View):
    template_name = 'tutor/tutor_enrollments.html'

    def get(self, request):
        
        enrollments = Enrollment.objects.filter(tutor=request.user)
        context = {
            'enrollments': enrollments
        }
        return render(request, self.template_name, context)

def submit_ticket(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    # Check user is respective tutor or student 
    if request.user not in [enrollment.approved_request.student, enrollment.tutor]:
        raise PermissionDenied("You do not have permission submit a ticket for this enrollment.")

    """Handle ticket submission."""
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.enrollment = enrollment
            ticket.user = request.user
            # Save the ticket with status 'Pending'
            ticket.status = TicketStatus.PENDING
            ticket.save()

            messages.success(request, "Your ticket has been submitted successfully.")
            return redirect('dashboard') 

        else:
            messages.error(request, "There was an error with your ticket submission. Please try again.")
    else:
        form = TicketForm()


    return render(request, 'submit_ticket.html', {'form': form, 'form': form, 'enrollment': enrollment})

def my_tickets(request):
    """Display tickets submitted by the logged-in user."""
    tickets = Ticket.objects.filter(user=request.user)
        # If no tickets are found, render with a message saying 'No tickets found'
    if not tickets:
        return render(request, 'my_tickets.html', {'tickets': tickets, 'message': 'No tickets found'})

    return render(request, 'my_tickets.html', {'tickets': tickets})