from django.urls import path

from . import views

urlpatterns = {
    path("get_webhook", views.get_webhook, name="get_webhook"),
    path("webhook", views.webhook, name="webhook"),
    path("", views.index, name="index")
}
