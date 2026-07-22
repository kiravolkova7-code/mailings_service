# from django.urls import path
# from django.contrib.auth import views as auth_views
# from .views import RegisterView
#
# urlpatterns = [
#     # Регистрация нашего ученика
#     path('register/', RegisterView.as_view(), name='register'),
#
#     # Вход и выход (берем стандартные)
#     path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
#     path('logout/', auth_views.LogoutView.as_view(), name='logout'),
#
#     # Восстановление пароля (стандартные шаги)
#     path('password_reset/', auth_views.PasswordResetView.as_view(
#         template_name='registration/password_reset.html',
#         email_template_name='registration/password_reset_email.html'
#     ), name='password_reset'),
#     path('password_reset/done/',
#          auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
#          name='password_reset_done'),
#     path('reset/<uidb64>/<token>/',
#          auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
#          name='password_reset_confirm'),
#     path('reset/done/',
#          auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
#          name='password_reset_complete'),
# ]