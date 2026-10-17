from django.urls import path

from . import views

urlpatterns = [
    path('admin/rate-cards/', views.AdminRateCardListCreateView.as_view(), name='admin-rate-cards'),
    path('admin/rate-cards/<uuid:pk>/activate/', views.AdminRateCardActivateView.as_view(),
         name='admin-rate-card-activate'),
]
