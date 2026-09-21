from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages

from recipients.forms import RecipientForm, MessageForm
from recipients.models import Recipients, Message
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

# --- БАЗОВЫЕ МИКСИНЫ ---


class OwnerOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return hasattr(obj, "created_by") and obj.created_by == self.request.user


class ManagerAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name="Менеджер").exists()


# --- 1. УПРАВЛЕНИЕ КЛИЕНТАМИ ---
@method_decorator(cache_page(60 * 10), name="dispatch")
class RecipientList(LoginRequiredMixin, ListView):
    template_name = "recipients_list.html"
    model = Recipients
    paginate_by = 20

    def get_queryset(self):
        qs = Recipients.objects.all()

        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request

        if view_for_manager.test_func():
            return qs

        if hasattr(Recipients, "created_by"):
            return qs.filter(created_by=self.request.user)

        return qs.none()


@method_decorator(cache_page(60 * 10), name="dispatch")
class RecipientsDetailView(LoginRequiredMixin, OwnerOnlyMixin, DetailView):
    model = Recipients
    template_name = "recipient_detail.html"
    context_object_name = "recipient"


class RecipientsCreateView(LoginRequiredMixin, CreateView):
    model = Recipients
    form_class = RecipientForm
    template_name = "recipient_form.html"
    success_url = reverse_lazy("recipients:recipients-list")

    def dispatch(self, request, *args, **kwargs):
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = request
        if view_for_manager.test_func():
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied("Менеджеры управляют клиентами через глобальный список.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if hasattr(self.model, "created_by"):
            form.instance.created_by = self.request.user

        response = super().form_valid(form)
        messages.success(self.request, f"Получатель '{self.object.email}' добавлен.")
        return response


class RecipientsUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipients
    form_class = RecipientForm
    template_name = "recipient_form.html"
    success_url = reverse_lazy("recipients:recipients-list")

    def get_queryset(self):
        qs = super().get_queryset()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request
        if not view_for_manager.test_func() and hasattr(Recipients, "created_by"):
            qs = qs.filter(created_by=self.request.user)
        return qs

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = request
        if not view_for_manager.test_func():
            if hasattr(obj, "created_by") and obj.created_by != request.user:
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = self.get_object()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request
        if not view_for_manager.test_func():
            if hasattr(obj, "created_by") and obj.created_by != self.request.user:
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().form_valid(form)


class RecipientsDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipients
    template_name = "recipient_delete.html"
    context_object_name = "recipient"
    success_url = reverse_lazy("recipients:recipients-list")

    def get_queryset(self):
        qs = super().get_queryset()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request
        if not view_for_manager.test_func() and hasattr(Recipients, "created_by"):
            qs = qs.filter(created_by=self.request.user)
        return qs

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = request
        if not view_for_manager.test_func():
            if hasattr(obj, "created_by") and obj.created_by != request.user:
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


# --- 2. УПРАВЛЕНИЕ СООБЩЕНИЯМИ ---
@method_decorator(cache_page(60 * 10), name="dispatch")
class MessageList(LoginRequiredMixin, ListView):
    template_name = "message_list.html"
    model = Message
    paginate_by = 20

    context_object_name = "messages"

    def get_queryset(self):
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request

        if view_for_manager.test_func():
            return Message.objects.all()

        if hasattr(Message, "created_by"):
            return Message.objects.filter(created_by=self.request.user)

        return Message.objects.none()


@method_decorator(cache_page(60 * 10), name="dispatch")
class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = "message_detail.html"
    context_object_name = "message"

    def get_queryset(self):
        qs = super().get_queryset()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request

        if view_for_manager.test_func():
            return qs

        if hasattr(Message, "created_by"):
            return qs.filter(created_by=self.request.user)
        return qs.none()


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "message_form.html"
    success_url = reverse_lazy("recipients:message-list")

    def dispatch(self, request, *args, **kwargs):
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = request
        if view_for_manager.test_func():
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied("Менеджеры создают сообщения через общий пул.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if hasattr(self.model, "created_by"):
            form.instance.created_by = self.request.user

        response = super().form_valid(form)
        messages.success(self.request, f"Письмо '{self.object.subject}' создано.")
        return response


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "message_form.html"
    success_url = reverse_lazy("recipients:message-list")

    def get_queryset(self):
        qs = super().get_queryset()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request
        if not view_for_manager.test_func() and hasattr(Message, "created_by"):
            qs = qs.filter(created_by=self.request.user)
        return qs

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = request
        if not view_for_manager.test_func():
            if hasattr(obj, "created_by") and obj.created_by != request.user:
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = self.get_object()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request
        if not view_for_manager.test_func():
            if hasattr(obj, "created_by") and obj.created_by != self.request.user:
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "message_delete.html"
    context_object_name = "message"
    success_url = reverse_lazy("recipients:message-list")

    def get_queryset(self):
        qs = super().get_queryset()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = self.request
        if not view_for_manager.test_func() and hasattr(Message, "created_by"):
            qs = qs.filter(created_by=self.request.user)
        return qs

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        view_for_manager = ManagerAccessMixin()
        view_for_manager.request = request
        if not view_for_manager.test_func():
            if hasattr(obj, "created_by") and obj.created_by != request.user:
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
