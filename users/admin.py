# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms

from .models import User


class UserCreationForm(forms.ModelForm):
    """
    Форма для создания нового пользователя через админку.
    Так как username отсутствует, мы оставляем только поле email и два ввода пароля.
    """
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput,
        help_text='Введите тот же пароль, что и выше, для подтверждения.'
    )

    class Meta:
        model = User
        fields = ('email',)  # Показываем только email при создании

    def clean_password2(self):
        # Проверяем совпадение паролей
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return password2

    def save(self, commit=True):
        # Сохраняем пользователя с хешированным паролем
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """
    Форма для изменения данных существующего пользователя.
    Поле пароля делаем "только для чтения" (хеш), чтобы случайно его не сломать.
    """
    password = ReadOnlyPasswordHashField(
        widget=forms.PasswordInput(attrs={'readonly': 'readonly'}),
        help_text='Хешированный пароль. Чтобы изменить пароль, используйте <a href="../../password/">специальную ссылку</a>.'
    )

    class Meta:
        model = User
        fields = '__all__'

    def clean_password(self):
        # При сохранении формы игнорируем ввод в поле пароля (оно readonly),
        # иначе старый хеш перезатрется пустотой или новым значением некорректно.
        return self.initial['password']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Указываем наши кастомные формы
    form = UserChangeForm
    add_form = UserCreationForm

    # Настройка отображения списка пользователей
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    # Поля для поиска
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    # Группировка полей на странице редактирования
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    # Группировка полей на странице СОЗДАНИЯ пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )