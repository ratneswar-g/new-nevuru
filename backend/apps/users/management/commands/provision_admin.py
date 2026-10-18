"""
Provision (or promote) an administrator bound to a Firebase UID.

Authentication stays strictly UID-based: the UID is read from the Firebase
console after the person has signed in once with their phone number.

    python manage.py provision_admin --phone +919876543210 --firebase-uid <UID> --first-name Asha
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.audit.services import record_audit
from apps.users.models import User, UserRole


class Command(BaseCommand):
    help = 'Create or update an ADMIN user bound to a Firebase UID.'

    def add_arguments(self, parser):
        parser.add_argument('--phone', required=True, help='E.164 phone number, e.g. +919876543210')
        parser.add_argument('--firebase-uid', required=True)
        parser.add_argument('--first-name', default='')
        parser.add_argument('--last-name', default='')

    @transaction.atomic
    def handle(self, *args, **opts):
        phone, uid = opts['phone'].strip(), opts['firebase_uid'].strip()
        if not phone.startswith('+') or not phone[1:].isdigit():
            raise CommandError('Phone must be E.164 (e.g. +919876543210).')
        clash = User.objects.filter(firebase_uid=uid).exclude(phone_number=phone).first()
        if clash:
            raise CommandError('That Firebase UID is already bound to a different account.')

        user = User.objects.filter(phone_number=phone).first()
        created = user is None
        if created:
            user = User.objects.create_user(phone_number=phone, role=UserRole.ADMIN, firebase_uid=uid,
                                            is_staff=True, first_name=opts['first_name'],
                                            last_name=opts['last_name'])
        else:
            previous = {'role': user.role, 'firebase_uid_set': bool(user.firebase_uid)}
            user.role, user.firebase_uid, user.is_staff, user.is_active = UserRole.ADMIN, uid, True, True
            user.save()
        record_audit(actor=None, action='ADMIN_PROVISIONED', resource_type='User', resource_id=user.id,
                     previous=None if created else previous, new={'role': 'ADMIN'})
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"} admin {phone}.'))
