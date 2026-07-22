from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("mailing.urls", namespace="home")),
    path("recipients/", include("recipients.urls", namespace="recipients")),
    path("message/", include("recipients.urls", namespace="message")),
    path("mailings/", include("mailing.urls", namespace="mailings")),
    path("accounts/", include("allauth.urls")),
]
