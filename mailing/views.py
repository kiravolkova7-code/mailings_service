import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView, TemplateView
from django.utils import timezone
from .forms import MailingForm
from .models import Mailing
from recipients.models import Recipients
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Count

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


class ManagerOrAuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser


class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 20

    def get_queryset(self):
        return Mailing.objects.select_related('message').prefetch_related('recipients').order_by('-start_time')


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self):
        return Mailing.objects.select_related('message').prefetch_related('recipients', 'logs__recipient')


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_form.html"
    success_url = reverse_lazy('mailings:mailing-list')

    def form_valid(self, form):
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    fields = ['message', 'recipients', 'start_time', 'end_time']
    template_name = "mailing_form.html"
    success_url = reverse_lazy('mailings:mailing-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Рассылка '#{self.object.pk}' успешно сохранена.")
        return response


def send_mailing_manually(request, pk):
    """Представление для кнопки 'Запустить рассылку вручную'."""
    mailing = get_object_or_404(Mailing, pk=pk)

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
            messages.warning(request,
                             f"Рассылка выполнена с ошибками ({failed_logs}/{total_logs} писем). Подробности — во вкладке «Логи».")
        elif total_logs > 0:
            messages.success(request, f"Рассылка успешно завершено. Отправлено {total_logs} писем.")
        else:
            messages.info(request, "Рассылка проверена, но валидных получателей не найдено.")

    except Exception as e:
        messages.error(request, f"Критическая ошибка системы при запуске: {str(e)}")
        logger.exception("Критическая ошибка в send_mailing_manually")

    return redirect(reverse_lazy('mailings:mailing-update', kwargs={'pk': pk}))


class MailingDeleteView(LoginRequiredMixin, ManagerOrAuthorRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing_delete.html"
    context_object_name = "mailing"
    success_url = reverse_lazy('mailings:mailing-list')
