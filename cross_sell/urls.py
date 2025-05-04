from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("cross-sell/workflow", views.create_workflow, name="create_workflow"),
    path("cross-sell/workflow/list", views.list_shop_workflows, name="list_shop_workflows")
]
