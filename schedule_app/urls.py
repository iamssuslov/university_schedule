from django.urls import path
from . import views

urlpatterns = [
    path('schedule/', views.schedule_view, name='schedule'),
    path('attendance/<int:schedule_id>/', views.mark_attendance, name='mark_attendance'),
    path('schedule/<int:schedule_id>/generate_code/', views.generate_code, name='generate_code'),
    path('schedule/<int:schedule_id>/confirm_attendance/', views.confirm_attendance, name='confirm_attendance'),
]
