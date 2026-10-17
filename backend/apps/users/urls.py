from django.urls import path

from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('me/', views.MeView.as_view(), name='me'),
    path('me/customer-profile/', views.CustomerProfileView.as_view(), name='customer-profile'),
    path('me/family-helpers/', views.FamilyHelperListCreateView.as_view(), name='family-helpers'),
    path('me/family-helpers/<uuid:pk>/', views.FamilyHelperDeleteView.as_view(), name='family-helper-delete'),
]
