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
    user = request.user
    schedules = []
    attendance_attempts = {}  # Словарь для хранения количества оставшихся попыток

    if user.user_type == 'student':

        schedules = Schedule.objects.filter(course__students=user, date__gte=now().date()).order_by('date', 'time')

        for schedule in schedules:
            attendance = schedule.attendance_set.filter(student=user).first()
            schedule.attendance_status = attendance.is_present if attendance else None

            # Добавляем в словарь оставшиеся попытки для каждого расписания
            session_key = f"attendance_attempts_{schedule.id}"
            attendance_attempts[schedule.id] = request.session.get(session_key, 3)

    elif user.user_type == 'teacher':

        schedules = Schedule.objects.filter(course__teacher=user, date__gte=now().date()).order_by('date', 'time')

        for schedule in schedules:
            if schedule.attendance_code is None:
                schedule.generate_attendance_code()

    # Создаём список словарей с данными для шаблона
    schedule_data = []
    for schedule in schedules:
        schedule_data.append({
            'schedule': schedule,
            'attendance_attempts': attendance_attempts.get(schedule.id, 3),
        })

    context = {
        'schedule_data': schedule_data,
    }
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

    MAX_ATTEMPTS = 3  # Максимальное количество попыток ввода кода
    session_key = f"attendance_attempts_{schedule_id}"  # Уникальный ключ для сохранения попыток

    # Если это POST-запрос
    if request.method == 'POST':
        entered_code = request.POST.get('code')
        schedule = get_object_or_404(Schedule, id=schedule_id)

        # Получаем количество оставшихся попыток из сессии
        attempts = request.session.get(session_key, MAX_ATTEMPTS)

        # Пытаемся найти запись посещаемости для текущего студента
        attendance, created = Attendance.objects.get_or_create(schedule=schedule, student=request.user)

        if attendance.is_present:
            # Если уже отмечено присутствие
            messages.info(request, "Вы уже подтвердили присутствие на это занятие.")
        elif attempts > 0:
            # Проверяем введенный код
            if entered_code == schedule.attendance_code:
                # Код правильный, отмечаем присутствие
                attendance.is_present = True
                attendance.confirmed_at = now()  # сохраняем время подтверждения
                attendance.save()
                messages.success(request, "Присутствие успешно подтверждено.")
            else:
                # Код неправильный, уменьшаем количество попыток
                attempts -= 1
                request.session[session_key] = attempts  # Обновляем количество попыток в сессии

                if attempts > 0:
                    messages.error(request, f"Неверный код. Осталось попыток: {attempts}.")
                else:
                    messages.error(request, "Попытки ввода исчерпаны. Вы больше не можете вводить код.")
        else:
            # Если попытки исчерпаны
            messages.error(request, "Вы больше не можете вводить код. Попытки исчерпаны.")

    return redirect('schedule')
