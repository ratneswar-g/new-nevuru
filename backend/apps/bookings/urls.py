from django.urls import path

from . import admin_views as a
from . import views as v

urlpatterns = [
    path('bookings/quote/', v.QuoteView.as_view(), name='booking-quote'),
    path('bookings/', v.BookingListCreateView.as_view(), name='bookings'),
    path('bookings/<uuid:pk>/', v.BookingDetailView.as_view(), name='booking-detail'),
    path('bookings/<uuid:pk>/confirm/', v.BookingConfirmView.as_view(), name='booking-confirm'),
    path('bookings/<uuid:pk>/cancel/', v.BookingCancelView.as_view(), name='booking-cancel'),
    path('bookings/<uuid:pk>/otp/<str:challenge_type>/', v.BookingOtpIssueView.as_view(), name='booking-otp'),
    path('bookings/<uuid:pk>/emergency/', v.BookingEmergencyView.as_view(), name='booking-emergency'),
    path('bookings/<uuid:pk>/incidents/', v.BookingIncidentView.as_view(), name='booking-incident'),
    # admin
    path('admin/bookings/', a.AdminBookingListView.as_view(), name='admin-bookings'),
    path('admin/bookings/<uuid:pk>/', a.AdminBookingDetailView.as_view(), name='admin-booking-detail'),
    path('admin/bookings/<uuid:pk>/assign/', a.AdminBookingAssignView.as_view(), name='admin-booking-assign'),
    path('admin/bookings/<uuid:pk>/unassign/', a.AdminBookingUnassignView.as_view(), name='admin-booking-unassign'),
    path('admin/bookings/<uuid:pk>/cancel/', a.AdminBookingCancelView.as_view(), name='admin-booking-cancel'),
    path('admin/bookings/<uuid:pk>/close/', a.AdminBookingCloseView.as_view(), name='admin-booking-close'),
    path('admin/dashboard/', a.AdminDashboardView.as_view(), name='admin-dashboard'),
]
