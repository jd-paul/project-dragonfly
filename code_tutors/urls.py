"""
URL configuration for code_tutors project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from tutorials import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('log_in/', views.LogInView.as_view(), name='log_in'),
    path('log_out/', views.log_out, name='log_out'),
    path('password/', views.PasswordView.as_view(), name='password'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
    path('become_a_tutor/', views.TutorSignUpView.as_view(), name='tutor_signup'),

    # Admin views
    path('manage_tutors/', views.ManageTutors.as_view(), name='manage_tutors'),
    path('manage_students/', views.ManageStudents.as_view(), name='manage_students'),
    path('manage_applications/', views.ManageApplications.as_view(), name='manage_applications'),

    path('lesson-request/<int:id>/', views.LessonRequestDetails, name='lesson_request_details'),
    path('update-request/<int:request_id>/<str:action>/', views.update_request_status, name='update_request_status'),

    #Student views
    path('offered_skill_list/', views.SkillListView.as_view(), name = 'offered_skill_list'),
    path('student_request_form/<int:skill_id>/', views.RequestLesson.as_view(), name = 'student_request_form'),
    path('your_requests/', views.YourRequestsView.as_view(), name = 'your_requests'),
    path('delete_your_request/<int:student_request_id>/', views.DeleteYourRequestView.as_view(), name = 'delete_your_request'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)