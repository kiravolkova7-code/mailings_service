from django.db import models
from django.conf import settings


class Recipients(models.Model):
    email = models.EmailField(unique=True, verbose_name="email", help_text="Введите адрес электронной почты")
    first_name = models.CharField(max_length=40, verbose_name="Имя", help_text="Укажите имя")
    surname = models.CharField(
        max_length=40, verbose_name="Отчество", blank=True, null=True, help_text="Укажите отчество (если есть)"
    )
    last_name = models.CharField(max_length=40, verbose_name="Фамилия", help_text="Укажите фамилию")
    comment = models.TextField(
        max_length=200, verbose_name="Комментарий", blank=True, null=True, help_text="Ваш комментарий (необязательно)"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_recipients",
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_name(self):
        parts = [self.first_name]
        if self.surname:
            parts.append(self.surname)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts).strip()


class Message(models.Model):
    subject = models.CharField(max_length=100, verbose_name="Тема письма", help_text="Укажите тему письма")
    body_message = models.TextField(max_length=1000, verbose_name="Текст письма", help_text="Введите текст письма")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages", verbose_name="Автор"
    )

    class Meta:
        verbose_name = "Письмо"
        verbose_name_plural = "Письма"

    def __str__(self):
        return self.subject
