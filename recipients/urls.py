from django.urls import path
from recipients.apps import RecipientsConfig

from recipients.views import (
    RecipientsDetailView, RecipientsCreateView,
    RecipientsUpdateView, RecipientsDeleteView,
    MessageDetailView, MessageCreateView,
    MessageDeleteView, MessageUpdateView,
    RecipientList, MessageList
)

app_name = RecipientsConfig.name

urlpatterns = [
    path("", RecipientList.as_view(), name="recipients-list"),
    path("<int:pk>/", RecipientsDetailView.as_view(), name="recipients-detail"),
    path("add/", RecipientsCreateView.as_view(), name="recipients-create"),
    path("<int:pk>/edit/", RecipientsUpdateView.as_view(), name="recipients-edit"),
    path("<int:pk>/delete/", RecipientsDeleteView.as_view(), name="recipients-delete"),
    path("messages/", MessageList.as_view(), name="message-list"),
    path("message/<int:pk>/", MessageDetailView.as_view(), name="message-detail"),
    path("message/add/", MessageCreateView.as_view(), name="message-create"),
    path("message/<int:pk>/edit/", MessageUpdateView.as_view(), name="message-edit"),
    path("message/<int:pk>/delete/", MessageDeleteView.as_view(), name="message-delete"),
    ]
