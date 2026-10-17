from rest_framework.permissions import BasePermission

from apps.users.models import UserRole


def _is_role(request, role):
    user = request.user
    return bool(user and user.is_authenticated and user.is_active and user.role == role)


class IsCustomerRole(BasePermission):
    message = 'Customer account required.'

    def has_permission(self, request, view):
        return _is_role(request, UserRole.CUSTOMER)


class IsCarePartnerRole(BasePermission):
    """Any Care Partner account, including those still pending verification."""

    message = 'Care Partner account required.'

    def has_permission(self, request, view):
        return _is_role(request, UserRole.CARE_PARTNER)


class IsApprovedCarePartner(BasePermission):
    """Care Partner whose KYC has been approved by an admin."""

    message = 'Approved Care Partner account required.'

    def has_permission(self, request, view):
        from apps.companions.models import CarePartnerStatus

        if not _is_role(request, UserRole.CARE_PARTNER):
            return False
        profile = getattr(request.user, 'care_partner_profile', None)
        return bool(profile and profile.status == CarePartnerStatus.APPROVED)


class IsAdminRole(BasePermission):
    message = 'Administrator account required.'

    def has_permission(self, request, view):
        return _is_role(request, UserRole.ADMIN)
