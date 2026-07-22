from django import forms
from django.contrib.auth import get_user_model
from allauth.account.utils import setup_user_email
from allauth.account.models import EmailAddress

User = get_user_model()


class CustomSignupForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={"placeholder": "Email", "class": "form-control", "required": True}),
    )

    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Придумайте пароль",
                "class": "form-control",
                "required": True,
            }
        ),
    )

    password2 = forms.CharField(
        label="Подтверждение пароля",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Повторите пароль",
                "class": "form-control",
                "required": True,
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "username" in self.fields:
            del self.fields["username"]

    def clean_email(self):
        """Проверка уникальности Email вручную"""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким Email уже существует.")
        return email

    def try_save(self, request):
        """
        Создает пользователя и настраивает его почтовый адрес.
        Возвращает кортеж (user, email_address) согласно требованиям SignupView.
        """
        user = User(
            email=self.cleaned_data["email"],
        )
        user.set_password(self.cleaned_data["password1"])
        user.save()
        email_address = setup_user_email(request, user, [])

        if not email_address.verified:
            email_address.verified = False
            email_address.save()

        return user, email_address

    def login_on_signup(self, request, user):
        from allauth.account import app_settings as account_settings
        from allauth.account.utils import perform_login

        perform_login(
            request,
            user,
            email_verification=account_settings.EMAIL_VERIFICATION,
            redirect_url=None,
            signal_kwargs={},
            signup=True,
        )

    def signup(self, request, user):
        """
        Вызывается после успешного создания пользователя.
        """
        pass
