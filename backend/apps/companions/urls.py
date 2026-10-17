from django.urls import path

from . import views as v

urlpatterns = [
    path('partner/me/', v.PartnerMeView.as_view(), name='partner-me'),
    path('partner/kyc/', v.PartnerKycSubmitView.as_view(), name='partner-kyc'),
    path('partner/vehicles/', v.PartnerVehicleListCreateView.as_view(), name='partner-vehicles'),
    path('partner/duty/', v.PartnerDutyView.as_view(), name='partner-duty'),
    path('partner/bookings/', v.PartnerBookingListView.as_view(), name='partner-bookings'),
    path('partner/bookings/<uuid:pk>/', v.PartnerBookingDetailView.as_view(), name='partner-booking-detail'),
    path('partner/bookings/<uuid:pk>/arrive/', v.PartnerArriveView.as_view(), name='partner-arrive'),
    path('partner/bookings/<uuid:pk>/verify-pickup/', v.PartnerVerifyPickupView.as_view(), name='partner-verify-pickup'),
    path('partner/bookings/<uuid:pk>/arrive-hospital/', v.PartnerArriveHospitalView.as_view(), name='partner-arrive-hospital'),
    path('partner/bookings/<uuid:pk>/start-return/', v.PartnerStartReturnView.as_view(), name='partner-start-return'),
    path('partner/bookings/<uuid:pk>/complete/', v.PartnerCompleteView.as_view(), name='partner-complete'),
    path('partner/bookings/<uuid:pk>/emergency/', v.PartnerEmergencyView.as_view(), name='partner-emergency'),
    path('partner/bookings/<uuid:pk>/incidents/', v.PartnerIncidentView.as_view(), name='partner-incident'),
    # admin
    path('admin/partners/', v.AdminPartnerListView.as_view(), name='admin-partners'),
    path('admin/partners/<uuid:pk>/approve/', v.AdminPartnerApproveView.as_view(), name='admin-partner-approve'),
    path('admin/partners/<uuid:pk>/reject/', v.AdminPartnerRejectView.as_view(), name='admin-partner-reject'),
    path('admin/partners/<uuid:pk>/suspend/', v.AdminPartnerSuspendView.as_view(), name='admin-partner-suspend'),
    path('admin/vehicles/<uuid:pk>/verify/', v.AdminVehicleVerifyView.as_view(), name='admin-vehicle-verify'),
]
