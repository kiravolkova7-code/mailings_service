from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from .forms import MailingForm

import locale
from django.views.generic import TemplateView
from django.utils import timezone
from mailing.models import Mailing
from recipients.models import Recipients


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
            'total_mailings': total_mailings,
            'active_mailings': active_mailings,
            'unique_recipients': unique_recipients,
        })

        return context

    @staticmethod
    def _format_number(value: int) -> str:
        """
        Вспомогательный метод для форматирования целых чисел.
        Использует настройки текущей локали ОС.
        """
        if value is None:
            return "—"

        formatted = locale.format_string("%d", value, grouping=True)
        return formatted


class ManagerOrAuthorRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав: автор или суперпользователь."""

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.author == self.request.user


class MailingListView(LoginRequiredMixin, ListView):
    """Список всех рассылок."""
    model = Mailing
    template_name = "mailing:mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 20

    def get_queryset(self):
        return Mailing.objects.select_related('message').prefetch_related('recipients').order_by('-start_time')


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр рассылки."""
    model = Mailing
    template_name = "mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self):
        return Mailing.objects.select_related('message').prefetch_related('recipients')


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки."""
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_form.html"
    success_url = reverse_lazy('mailings:list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, ManagerOrAuthorRequiredMixin, UpdateView):
    """Редактирование существующей рассылки."""
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_form.html"
    context_object_name = "mailing"
    success_url = reverse_lazy('mailings:list')


class MailingDeleteView(LoginRequiredMixin, ManagerOrAuthorRequiredMixin, DeleteView):
    """Удаление рассылки."""
    model = Mailing
    template_name = "mailing_confirm_delete.html"
    context_object_name = "mailing"
    success_url = reverse_lazy('mailings:list')


