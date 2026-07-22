import logging
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.utils import timezone
from .forms import MailingForm
from .models import Mailing, SendLog
from recipients.models import Recipients
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db import models

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        total_mailings = Mailing.objects.count()
        active_mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now
        ).count()
        unique_recipients = Recipients.objects.count()

        context.update({
            'total_mailings': self._format_number(total_mailings),
            'active_mailings': self._format_number(active_mailings),
            'unique_recipients': self._format_number(unique_recipients),
        })
        return context

    @staticmethod
    def _format_number(value: int) -> str:
        if value is None:
            return "—"
        return f"{value:,}".replace(",", " ")


# --- МИКСИНЫ ДЛЯ ПРАВ ДОСТУПА ---

class IsOwnerMixin(UserPassesTestMixin):
    """Разрешает доступ к объекту только его владельцу."""

    def test_func(self):
        obj = self.get_object()
        return obj.created_by == self.request.user


class ManagerAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Проверяет наличие группы 'Менеджер' у пользователя (для глобальных панелей)."""

    def test_func(self):
        return self.request.user.groups.filter(name='Менеджер').exists()


class IsManagerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Новый миксин: Проверяет наличие группы 'Менеджер' у пользователя (для переиспользования во views)."""

    def test_func(self):
        return self.request.user.groups.filter(name='Менеджер').exists()


# --- СПИСКИ И ОТЧЕТЫ ---

class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 20

    def get_queryset(self):
        qs = Mailing.objects.select_related('message').prefetch_related('recipients')

        # Используем менеджерский миксин для логики выборки
        view_for_manager = IsManagerMixin()
        view_for_manager.request = self.request

        if view_for_manager.test_func():
            return qs.order_by('-start_time')

        return qs.filter(created_by=self.request.user).order_by('-start_time')


class ReportListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing_report.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        base_qs = Mailing.objects.select_related('message', 'created_by').annotate(
            logs_count=Count('logs'),
            success_count=Count('logs', filter=Q(logs__status='success')),
            fail_count=Count('logs', filter=Q(logs__status='Не успешно'))
        )

        view_for_manager = IsManagerMixin()
        view_for_manager.request = self.request

        if view_for_manager.test_func():
            return base_qs.order_by('-start_time')

        return base_qs.filter(created_by=self.request.user).order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reports_qs = context['reports']

        context.update({
            'total_reports': reports_qs.count(),
            'total_success': sum(report.success_count for report in reports_qs),
            'total_fail': sum(report.fail_count for report in reports_qs),
            'search_query': self.request.GET.get('q', ''),
        })
        return context


# --- ДЕТАЛИ И РЕДАКТИРОВАНИЕ ---

class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self):
        qs = Mailing.objects.select_related('message').prefetch_related('recipients', 'logs__recipient')

        view_for_manager = IsManagerMixin()
        view_for_manager.request = self.request

        if view_for_manager.test_func():
            return qs

        return qs.filter(created_by=self.request.user)


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_form.html"
    success_url = reverse_lazy('mailings:mailing-list')

    def dispatch(self, request, *args, **kwargs):
        # Используем переиспользуемый миксин IsManagerMixin
        view_for_manager = IsManagerMixin()
        view_for_manager.request = request

        if view_for_manager.test_func():
            messages.info(request, "Создание рассылок доступно из панели менеджера.")
            return redirect(reverse_lazy('mailings:manager-dashboard'))

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            print("[DEBUG] Форма валидна. Данные:", form.cleaned_data)  # Вывод в консоль runserver
            logger.info(f"Пользователь {self.request.user} пытается сохранить рассылку.")

            form.instance.created_by = self.request.user
            response = super().form_valid(form)  # Здесь происходит INSERT в БД

            logger.info(f"Рассылка #{self.object.pk} успешно сохранена.")
            messages.success(self.request, f"Рассылка '#{self.object.pk}' создана.")
            return response

        except Exception as e:
            logger.exception("КРИТИЧЕСКАЯ ОШИБКА ПРИ СОХРАНЕНИИ РАССЫЛКИ")
            messages.error(self.request, f"Системная ошибка: {e}")
            return redirect(reverse_lazy('mailings:mailing-create'))


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    fields = ['message', 'recipients', 'start_time', 'end_time']
    template_name = "mailing_form.html"
    success_url = reverse_lazy('mailings:mailing-list')

    def get_queryset(self):
        qs = super().get_queryset()

        view_for_manager = IsManagerMixin()
        view_for_manager.request = self.request

        if not view_for_manager.test_func():
            qs = qs.filter(created_by=self.request.user)
        return qs

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        view_for_manager = IsManagerMixin()
        view_for_manager.request = request

        if not view_for_manager.test_func() and obj.created_by != request.user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = self.get_object()

        view_for_manager = IsManagerMixin()
        view_for_manager.request = self.request
        if not view_for_manager.test_func() and obj.created_by != self.request.user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        response = super().form_valid(form)
        messages.success(self.request, f"Рассылка '#{self.object.pk}' успешно сохранена.")
        return response


def send_mailing_manually(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)

    if not (
            request.user.is_superuser or
            request.user.groups.filter(name='Менеджер').exists() or
            mailing.created_by == request.user
    ):
        messages.error(request, "У вас нет прав для запуска этой рассылки.")
        return redirect(reverse_lazy('mailings:mailing-list'))

    now = timezone.now()
    if not (mailing.start_time <= now <= mailing.end_time):
        allowed_window = f"{mailing.start_time.strftime('%d.%m.%Y %H:%M')} - {mailing.end_time.strftime('%d.%m.%Y %H:%M')}"
        messages.error(
            request,
            f"Отправка невозможна вне заданного окна времени ({allowed_window}). Текущее время: {now.strftime('%d.%m.%Y %H:%M')}."
        )
        return redirect(reverse_lazy('mailings:mailing-update', kwargs={'pk': pk}))

    try:
        from .services import execute_mailing
        execute_mailing(mailing.id)

        failed_logs = mailing.logs.filter(status='Не успешно').count()
        total_logs = mailing.logs.count()

        if failed_logs > 0 and total_logs > 0:
            messages.warning(request, f"Рассылка выполнена с ошибками ({failed_logs}/{total_logs} писем).")
        elif total_logs > 0:
            messages.success(request, f"Рассылка успешно завершена. Отправлено {total_logs} писем.")
        else:
            messages.info(request, "Рассылка проверена, но валидных получателей не найдено.")

    except Exception as e:
        messages.error(request, f"Критическая ошибка системы при запуске: {str(e)}")
        logger.exception("Критическая ошибка в send_mailing_manually")

    return redirect(reverse_lazy('mailings:mailing-update', kwargs={'pk': pk}))


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing_delete.html"
    context_object_name = "mailing"
    success_url = reverse_lazy('mailings:mailing-list')

    def get_queryset(self):
        qs = super().get_queryset()

        view_for_manager = IsManagerMixin()
        view_for_manager.request = self.request

        if not view_for_manager.test_func():
            qs = qs.filter(created_by=self.request.user)
        return qs

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        view_for_manager = IsManagerMixin()
        view_for_manager.request = request

        if not view_for_manager.test_func() and obj.created_by != request.user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class DashboardView(ManagerAccessMixin, TemplateView):
    template_name = "manager/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # Глобальные счетчики (без фильтрации по пользователю)
        total_mailings = Mailing.objects.count()

        # Активные считаем через Q-объекты напрямую в БД (это быстро)
        active_mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now
        ).count()

        total_recipients = Recipients.objects.count()

        # --- ИСПРАВЛЕННЫЙ БЛОК СТАТУСОВ ---
        # Получаем все рассылки одним запросом
        all_mailings = Mailing.objects.all()

        # Считаем статусы в Python, используя ваше свойство @property status
        # Это обходит проблему конфликта имен свойства и SQL-аннотации
        status_summary = {
            'created': 0,
            'running': 0,
            'finished': 0,
        }

        for mailing in all_mailings:
            mail_status = mailing.status
            if mail_status in status_summary:
                status_summary[mail_status] += 1

        # Преобразуем словарь в список словарей для цикла {% for %} в шаблоне
        status_counts = [
            {'status': key.title(), 'count': value}
            for key, value in status_summary.items()
        ]

        # Общая статистика логов по всей системе
        logs_agg = SendLog.objects.aggregate(
            total_attempts=Count('id'),
            successes=Count('id', filter=Q(status='success')),
            failures=Count('id', filter=Q(status='Не успешно'))
        )

        context.update({
            'total_mailings': total_mailings,
            'active_mailings': active_mailings,
            'total_recipients': total_recipients,
            'status_counts': status_counts,
            'logs_agg': logs_agg,
        })
        return context


class AllMailingsListView(ManagerAccessMixin, ListView):
    model = Mailing
    template_name = "manager/all_mailings.html"
    context_object_name = "all_mailings"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            Mailing.objects.select_related('message', 'created_by')
            .prefetch_related('recipients')
            .order_by('-start_time')
        )

        print(f"[DEBUG] AllMailingsListView: QuerySet сформирован. Найдено объектов: {qs.count()}")

        return qs


class AllRecipientsListView(ManagerAccessMixin, ListView):
    model = Recipients
    template_name = "manager/all_recipients.html"
    context_object_name = "all_recipients"
    paginate_by = 50

    def get_queryset(self):
        if hasattr(Recipients, 'created_by'):
            return Recipients.objects.select_related('created_by').order_by('email')
        return Recipients.objects.all().order_by('email')