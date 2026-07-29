"""
File: BitByte-Marketing/backend/accounts/management/commands/create_dummy_logins.py

Purpose : Admin, Dealer, Sub Dealer, Promotor ku RANDOM ah "today login" (last_login)
          set pannurathukku — Active/Inactive pie chart testing ku dummy data.
          Customer touch pannaathu (login mandatory illa nu already decide pannirukom).

Args    :
    --percent      Evlo % users active-ah irukanumo (default: 30)
    --role         Specific role mattum target pannanumna (admin/dealer/sub_dealer/promotor/all)
    --reset        Ella users oda last_login um NULL pannitu, appuram fresh-ah random set pannum

Run:
    python manage.py create_dummy_logins --percent 30
    python manage.py create_dummy_logins --percent 50 --role admin
    python manage.py create_dummy_logins --percent 40 --reset
"""
import random
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import AdminProfile, DealerProfile, SubDealerProfile, PromotorProfile

ROLE_MODELS = {
    'admin': AdminProfile,
    'dealer': DealerProfile,
    'sub_dealer': SubDealerProfile,
    'promotor': PromotorProfile,
}


class Command(BaseCommand):
    help = 'Set RANDOM last_login (today) for a percentage of admin/dealer/sub_dealer/promotor users — dummy Active/Inactive testing'

    def add_arguments(self, parser):
        parser.add_argument('--percent', type=int, default=30, help='Percentage of users to mark active today (0-100)')
        parser.add_argument('--role', type=str, default='all', choices=['admin', 'dealer', 'sub_dealer', 'promotor', 'all'],
                             help='Target a specific role, or all (default: all)')
        parser.add_argument('--reset', action='store_true',
                             help='Clear all last_login first, then randomly set active percent fresh')

    def handle(self, *args, **options):
        percent = max(0, min(100, options['percent']))
        role_arg = options['role']
        reset = options['reset']

        target_models = ROLE_MODELS if role_arg == 'all' else {role_arg: ROLE_MODELS[role_arg]}

        all_users = []
        for role_name, Model in target_models.items():
            profiles = Model.objects.select_related('user').all()
            for p in profiles:
                all_users.append((role_name, p.user))

        if not all_users:
            self.stdout.write(self.style.ERROR("No users found for selected role(s)."))
            return

        if reset:
            for role_name, user in all_users:
                user.last_login = None
                user.save(update_fields=['last_login'])
            self.stdout.write(self.style.WARNING(f"Reset last_login for {len(all_users)} users."))

        random.shuffle(all_users)
        active_count = max(1, int(len(all_users) * percent / 100))
        selected = all_users[:active_count]

        now = timezone.now()
        for role_name, user in selected:
            # Today-oda within irukura random time (last 12 hours-ku ulla)
            user.last_login = now - timezone.timedelta(minutes=random.randint(0, 720))
            user.save(update_fields=['last_login'])

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! {len(selected)}/{len(all_users)} users ({percent}%) marked ACTIVE today."
        ))

        # Role-wise breakdown
        breakdown = {}
        for role_name, user in selected:
            breakdown[role_name] = breakdown.get(role_name, 0) + 1
        for role_name, count in breakdown.items():
            self.stdout.write(self.style.SUCCESS(f"  {role_name}: {count} active"))