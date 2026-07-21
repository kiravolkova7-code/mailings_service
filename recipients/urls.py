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
    path("list/", RecipientList.as_view(), name="recipient-list"),
    path("<int:pk>/", RecipientsDetailView.as_view(), name="recipient-detail"),
    path("add/", RecipientsCreateView.as_view(), name="recipient-add"),
    path("<int:pk>/edit/", RecipientsUpdateView.as_view(), name="recipient-edit"),
    path("<int:pk>/delete/", RecipientsDeleteView.as_view(), name="recipient-delete"),
    path("message/list/", MessageList.as_view(), name="message-list"),
    path("message/<int:pk>/", MessageDetailView.as_view(), name="message-detail"),
    path("message/add/", MessageCreateView.as_view(), name="message-add"),
    path("message/<int:pk>/edit/", MessageUpdateView.as_view(), name="message-edit"),
    path("message/<int:pk>/delete/", MessageDeleteView.as_view(), name="message-delete"),
    ]
