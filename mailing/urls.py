
from django.urls import path
from mailing.apps import MailingConfig
from .views import (
    MailingListView, MailingDetailView,
    MailingCreateView, MailingUpdateView,
    MailingDeleteView, HomeView, send_mailing_manually
)

app_name = MailingConfig.name

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('list/', MailingListView.as_view(), name='mailing-list'),
    path('<int:pk>/', MailingDetailView.as_view(), name='mailing-detail'),
    path('create/', MailingCreateView.as_view(), name='mailing-create'),
    path('<int:pk>/edit/', MailingUpdateView.as_view(), name='mailing-update'),
    path('<int:pk>/delete/', MailingDeleteView.as_view(), name='mailing-delete'),
    path('<int:pk>/send/', send_mailing_manually, name='send-mailing'),
]
