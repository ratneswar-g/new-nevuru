from django.urls import path

from . import views

urlpatterns = [
    path('admin/incidents/', views.AdminIncidentListView.as_view(), name='admin-incidents'),
    path('admin/incidents/<uuid:pk>/resolve/', views.AdminIncidentResolveView.as_view(),
         name='admin-incident-resolve'),
]
