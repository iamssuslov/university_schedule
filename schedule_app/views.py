from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Schedule, Attendance, User
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from django.contrib.auth import login


def home(request):
    return render(request, 'schedule_app/home.html')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # После регистрации автоматически авторизуем пользователя
            return redirect('home')  # Редирект на главную страницу
    else:
        form = UserRegisterForm()
    return render(request, 'schedule_app/register.html', {'form': form})


@login_required
def schedule_view(request):
    user: User = request.user
    if user.user_type == 'student':
        schedules = Schedule.objects.filter(course__in=request.user.course_set.all())
    elif user.user_type == 'teacher':
        schedules = Schedule.objects.filter(course__teacher=request.user)
    else:
        schedules = Schedule.objects.all()
    context = {'schedules': schedules}
    return render(request, 'schedule_app/schedule.html', context)


@login_required
def mark_attendance(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    if request.method == 'POST':
        students = schedule.course.students.filter(user_type='student')
        for student in students:
            is_present = request.POST.get(f'student_{student.id}', 'off') == 'on'
            Attendance.objects.update_or_create(
                student=student,
                schedule=schedule,
                defaults={'is_present': is_present}
            )
        return redirect('schedule')
    else:
        students = schedule.course.students.filter(user_type='student')
        context = {
            'schedule': schedule,
            'students': students,
        }
        return render(request, 'schedule_app/mark_attendance.html', context)


def stub_page(request):
    return HttpResponse("Доступ запрещён. Пожалуйста, войдите как суперпользователь.")
