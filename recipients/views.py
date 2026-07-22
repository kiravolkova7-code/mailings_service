from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from recipients.forms import RecipientForm, MessageForm
from recipients.models import Recipients, Message
from django.urls import reverse_lazy


# 1. Управление клиентами
class RecipientList(ListView):
    template_name = "recipients_list.html"
    model = Recipients



class RecipientsDetailView(DetailView):
    """Детальная страница товара."""

    model = Recipients
    template_name = "recipient_detail.html"
    context_object_name = "recipient"
    success_url = reverse_lazy('recipients:recipients-detail')


class RecipientsCreateView(CreateView):
    """Детальная страница товара."""

    model = Recipients
    form_class = RecipientForm
    template_name = "recipient_form.html"
    context_object_name = "recipient"
    success_url = reverse_lazy('recipients:recipients-list')


class RecipientsUpdateView(UpdateView):
    """Детальная страница товара."""

    model = Recipients
    form_class = RecipientForm
    template_name = "recipient_form.html"
    context_object_name = "recipient"
    success_url = reverse_lazy('recipients:recipients-list')


class RecipientsDeleteView(DeleteView):
    """Детальная страница товара."""

    model = Recipients
    template_name = "recipient_delete.html"
    context_object_name = "recipient"
    success_url = reverse_lazy('recipients:recipients-list')

# 2. Управление сообщениями
class MessageList(ListView):
    template_name = "message_list.html"
    model = Message


class MessageDetailView(DetailView):
    """Детальная страница товара."""

    model = Message
    template_name = "message_detail.html"
    context_object_name = "message"
    success_url = reverse_lazy('recipients:message-detail')


class MessageCreateView(CreateView):
    """Детальная страница товара."""

    model = Message
    form_class = MessageForm
    template_name = "message_form.html"
    context_object_name = "message"
    success_url = reverse_lazy('recipients:message-list')


class MessageUpdateView(UpdateView):
    """Детальная страница товара."""

    model = Message
    form_class = MessageForm
    template_name = "message_form.html"
    context_object_name = "message"
    success_url = reverse_lazy('recipients:message-list')


class MessageDeleteView(DeleteView):
    """Детальная страница товара."""

    model = Message
    template_name = "message_delete.html"
    context_object_name = "message"
    success_url = reverse_lazy('recipients:message-list')
