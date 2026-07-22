from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models as db_models
from django.contrib.auth import get_user_model

from config import settings

User = get_user_model()


class Mailing(db_models.Model):
    STATUS_CHOICES = [
        ("created", "Создана"),
        ("running", "Запущена"),
        ("finished", "Завершена"),
    ]

    start_time = db_models.DateTimeField(
        verbose_name="Дата и время начала отправки", help_text="С какого момента рассылка может быть запущена."
    )
    end_time = db_models.DateTimeField(
        verbose_name="Дата и время окончания отправки", help_text="До какого момента разрешено выполнять отправку."
    )
    message = db_models.ForeignKey(
        "recipients.Message", on_delete=db_models.PROTECT, related_name="mailings", verbose_name="Сообщение"
    )
    recipients = db_models.ManyToManyField(
        "recipients.Recipients", related_name="mailings", verbose_name="Получатели", blank=True
    )

    created_at = db_models.DateTimeField(auto_now_add=True, verbose_name="Создана в системе")
    updated_at = db_models.DateTimeField(auto_now=True, verbose_name="Обновлена в системе")

    created_by = db_models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=db_models.SET_NULL, verbose_name="Автор рассылки"
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-start_time"]

    def __str__(self):
        status_label = dict(self.STATUS_CHOICES).get(self.status, "Неизвестно")
        return f"Рассылка #{self.pk}: {self.message.subject} ({status_label})"

    @property
    def status(self):
        now = timezone.now()
        if now < self.start_time:
            return "created"
        elif self.start_time <= now <= self.end_time:
            return "running"
        else:
            return "finished"

    @property
    def total_attempts(self):
        """Общее количество попыток отправки (равно количеству записей в SendLog)"""
        return self.logs.count()

    @property
    def successful_attempts(self):
        """Количество успешных отправок"""
        return self.logs.filter(status="success").count()

    @property
    def failed_attempts(self):
        """Количество неуспешных отправок"""
        return self.logs.filter(status="Не успешно").count()

    @property
    def messages_sent(self):
        """Фактически доставленные сообщения. В вашей модели это дублирует success."""
        return self.successful_attempts

    def clean(self):
        super().clean()
        if self.start_time and self.start_time < timezone.now():
            raise ValidationError({"start_time": "Дата и время начала не могут быть в прошлом."})
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Дата и время начала должны быть раньше даты и времени окончания.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class SendLog(models.Model):
    STATUS_CHOICES = [
        ("success", ("Успешно")),
        ("Не успешно", ("Не успешно")),
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="logs", verbose_name=("Рассылка"))
    recipient = models.ForeignKey("recipients.Recipients", on_delete=models.CASCADE, verbose_name=("Получатель"))

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name=("Дата и время попытки"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name=("Статус"))
    server_response = models.TextField(blank=True, null=True, verbose_name=("Ответ почтового сервера"))

    class Meta:
        verbose_name = "Лог отправки"
        verbose_name_plural = "Логи отправок"
        ordering = ["-attempt_time"]
        indexes = [
            models.Index(fields=["mailing", "recipient"], name="mailing_recipient_idx"),
        ]

    def __str__(self):
        return f"#{self.id} | {self.mailing_id} -> {self.recipient.email} [{self.get_status_display()}]"
