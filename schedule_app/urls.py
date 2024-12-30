from django.urls import path
from . import views

urlpatterns = [
    path('schedule/', views.schedule_view, name='schedule'),
    path('attendance/<int:schedule_id>/', views.mark_attendance, name='mark_attendance'),
]