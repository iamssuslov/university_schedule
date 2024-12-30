from django.shortcuts import redirect
from django.urls import reverse


class AdminRestrictMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем, является ли пользователь суперпользователем
        if request.path.startswith(reverse('admin:index')) and not request.user.is_superuser:
            # Если нет, перенаправляем, например, на заглушку
            return redirect('stub_page')

        response = self.get_response(request)
        return response
