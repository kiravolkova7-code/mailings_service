from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from mailing.models import Mailing, SendLog
from .services import execute_mailing


class SendLogInline(admin.TabularInline):
    model = SendLog
    fields = ("recipient", "attempt_time", "status", "server_response")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("__str__", "start_time", "end_time", "status_column", "go_to_logs_link")

    list_filter = ("start_time", "end_time")

    search_fields = ("message__subject",)
    readonly_fields = ("created_at", "updated_at")
    actions = ["run_mailing_action"]
    inlines = [SendLogInline]

    def go_to_logs_link(self, obj):
        url = reverse("admin:mailing_sendlog_changelist") + f"?mailing__id__exact={obj.id}"
        return format_html('<a href="{}">Перейти к логам</a>', url)

    go_to_logs_link.short_description = "Логи"

    @admin.display(description="Статус", ordering="start_time")
    def status_column(self, obj):
        """Отображает статус в админке. Не является полем БД."""
        return dict(Mailing.STATUS_CHOICES).get(obj.status, "Неизвестно")

    def run_mailing_action(self, request, queryset):
        """Действие админки для массового запуска рассылок."""
        if queryset.count() != 1:
            self.message_user(request, "Можно запустить за раз только одну рассылку.", level="ERROR")
            return

        mailing = queryset.first()
        now = timezone.now()

        if not (mailing.start_time <= now <= mailing.end_time):
            allowed_window = (
                f"{mailing.start_time.strftime('%d.%m.%Y %H:%M')} - {mailing.end_time.strftime('%d.%m.%Y %H:%M')}"
            )
            error_msg = f"Текущее время вне допустимого окна отправки ({allowed_window})."
            self.message_user(request, error_msg, level="ERROR")
            return

        if now > mailing.end_time:
            self.message_user(request, "Нельзя запускать уже завершенные рассылки.", level="ERROR")
            return

        try:
            execute_mailing(mailing.pk)
            self.message_user(request, f"Рассылка #{mailing.pk} поставлена в очередь/выполнена.")
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.exception(f"Критическая ошибка при выполнении действия админки для рассылки #{mailing.pk}")
            self.message_user(request, f"Произошла системная ошибка: {e}", level="ERROR")

    run_mailing_action.short_description = "Запустить выбранную рассылку"


@admin.register(SendLog)
class SendLogAdmin(admin.ModelAdmin):
    list_display = ("mailing", "recipient", "attempt_time", "status")
    list_filter = ("status", "attempt_time")
    search_fields = ("recipient__email", "server_response")
    readonly_fields = ("attempt_time",)
