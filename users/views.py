
# from django.shortcuts import redirect
# from django.views.generic import CreateView
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
# from django.core.mail import send_mail
# from django.conf import settings
#
# # mailing/views.py
# from django.contrib.auth.decorators import login_required
# from django.utils.decorators import method_decorator
# from django.views.generic import ListView, CreateView, UpdateView, DeleteView
# from mailing.models import Mailing
# from mailing.forms import MailingForm
#
# from functools import wraps
# from django.http import HttpResponseForbidden
#
#
# class RegisterView(CreateView):
#     form_class = UserCreationForm
#     template_name = 'registration/register.html'
#
#     def form_valid(self, form):
#         user = form.save(commit=False)
#         # Сразу помечаем, что почта не подтверждена
#         user.is_active = False
#         user.save()
#
#         # Простейшее "письмо" админу о новом пользователе
#         # (в реальности здесь должна быть ссылка с токеном для самого юзера)
#         send_mail(
#             subject=f'Новый пользователь: {user.username}',
#             message=f'Пользователь {user.email} зарегистрировался. Проверьте почту перед активацией.',
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[settings.ADMIN_EMAIL],
#         )
#
#         return redirect('login')
#
#
# @method_decorator(login_required, name='dispatch')
# class MyMailingsListView(ListView):
#     model = Mailing
#     template_name = 'mailing/my_list.html'
#
#     def get_queryset(self):
#         # Пользователь видит ТОЛЬКО свои рассылки
#         return Mailing.objects.filter(created_by=self.request.user)
#
#
# @method_decorator(login_required, name='dispatch')
# class MailingCreateView(CreateView):
#     model = Mailing
#     form_class = MailingForm
#     template_name = 'mailing/form.html'
#
#     def form_valid(self, form):
#         # Автоматически подставляем текущего пользователя как автора
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)
#
#
# @method_decorator(login_required, name='dispatch')
# class MailingUpdateView(UpdateView):
#     model = Mailing
#     form_class = MailingForm
#     template_name = 'mailing/form.html'
#
#     def get_queryset(self):
#         # Разрешаем редактировать только свои рассылки
#         return Mailing.objects.filter(created_by=self.request.user)
#
#
# @method_decorator(login_required, name='dispatch')
# class MailingDeleteView(DeleteView):
#     model = Mailing
#     success_url = '/my-mailings/'  # Куда вернуться после удаления
#
#     def get_queryset(self):
#         return Mailing.objects.filter(created_by=self.request.user)
#
#
#
#
# def manager_required(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         if not request.user.groups.filter(name='managers').exists():
#             return HttpResponseForbidden("Доступ запрещен. Нужна роль Менеджера.")
#         return view_func(request, *args, **kwargs)
#     return _wrapped_view