from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Schedule, Attendance, User
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from django.contrib import messages
from django.contrib.auth import login
from django.utils.timezone import now


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
    schedules = []

    if user.user_type == 'student':
        # Получаем расписание для студентов
        schedules = Schedule.objects.filter(course__students=request.user)

        # Добавляем информацию о посещаемости в каждое расписание
        for schedule in schedules:
            attendance = schedule.attendance_set.filter(student=user).first()
            schedule.attendance_status = attendance.is_present if attendance else None
    elif user.user_type == 'teacher':
        # Получаем расписание для преподавателей
        schedules = Schedule.objects.filter(course__teacher=request.user)
        for schedule in schedules:
            if schedule.attendance_code is None:  # Генерация кода, если он не существует
                schedule.generate_attendance_code()
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


@login_required
def generate_code(request, schedule_id):
    if not request.user.is_authenticated or request.user.user_type != 'teacher':
        return JsonResponse({'error': 'Access denied'}, status=403)

    schedule = get_object_or_404(Schedule, id=schedule_id, course__teacher=request.user)
    schedule.generate_attendance_code()
    return JsonResponse({'message': 'Attendance code generated', 'code': schedule.attendance_code})


@login_required
def confirm_attendance(request, schedule_id):
    if not request.user.is_authenticated or request.user.user_type != 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method == 'POST':
        entered_code = request.POST.get('code')
        schedule = Schedule.objects.get(id=schedule_id)

        # Пытаемся найти все записи посещаемости для текущего студента и расписания
        attendance_queryset = Attendance.objects.filter(schedule=schedule, student=request.user)

        # Если запись уже существует, то обновляем ее
        if attendance_queryset.exists():
            attendance = attendance_queryset.first()  # Берем первую запись
        else:
            attendance = Attendance.objects.create(
                schedule=schedule,
                student=request.user
            )

        # Проверяем, была ли уже отмечена посещаемость
        if attendance.is_present:
            messages.info(request, "Вы уже отметили присутствие на это занятие.")
        elif entered_code == schedule.attendance_code:
            # Если код правильный, отмечаем посещаемость
            attendance.is_present = True
            attendance.confirmed_at = now()  # сохраняем время подтверждения
            attendance.save()
            messages.success(request, "Присутствие успешно подтверждено.")
        else:
            messages.error(request, "Неверный код. Попробуйте еще раз.")
    
    return redirect('schedule')  # Перенаправляем на страницу расписания
