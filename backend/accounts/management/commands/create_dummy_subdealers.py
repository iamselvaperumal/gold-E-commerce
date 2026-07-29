import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from accounts.models import User, DealerProfile, SubDealerProfile


FIRST_NAMES = [
    'Arun', 'Karthik', 'Vignesh', 'Prakash', 'Suresh', 'Ramesh', 'Vijay',
    'Senthil', 'Mani', 'Rajesh', 'Ganesh', 'Anand', 'Bala', 'Dinesh',
    'Elango', 'Gopal', 'Hari', 'Ilango', 'Jagan', 'Kannan', 'Loganathan',
    'Muthu', 'Naveen', 'Prasanna', 'Raja', 'Saravanan',
    'Tamil', 'Uday', 'Vasanth', 'Selvam', 'Dhanraj', 'Jai',
]

FATHER_NAMES = [
    'Ramesh', 'Rajasekar', 'Elangovan', 'Muthuraman', 'Chandrasekar',
    'Palaniappan', 'Govindaraj', 'Krishnamurthy', 'Sivakumar', 'Balasubramaniam',
    'Natarajan', 'Subramaniam', 'Manikandan', 'Selvaraj', 'Kaliyaperumal',
    'Duraisamy', 'Venkatesan', 'Perumal', 'Ganapathy', 'Rajendran',
]

CITIES = [
    ('Chennai', 'Chennai', 'Tamil Nadu'),
    ('Coimbatore', 'Coimbatore', 'Tamil Nadu'),
    ('Madurai', 'Madurai', 'Tamil Nadu'),
    ('Trichy', 'Tiruchirappalli', 'Tamil Nadu'),
    ('Salem', 'Salem', 'Tamil Nadu'),
    ('Erode', 'Erode', 'Tamil Nadu'),
    ('Vellore', 'Vellore', 'Tamil Nadu'),
    ('Tirunelveli', 'Tirunelveli', 'Tamil Nadu'),
    ('Namakkal', 'Namakkal', 'Tamil Nadu'),
    ('Karur', 'Karur', 'Tamil Nadu'),
]

INITIALS = ['S', 'K', 'M', 'A', 'R', 'V', 'P', 'G', 'D', 'T']

OCCUPATION_DETAILS = {
    'employee': ['Sales Executive', 'Field Officer', 'Area Coordinator'],
    'business': ['Small Shop Owner', 'Retail Trader', 'Local Merchant'],
    'others': ['Freelancer', 'Self Employed'],
}

DUMMY_PASSWORD = "Senthil@2026"


def random_dob():
    days_old = random.randint(22 * 365, 46 * 365)
    return date.today() - timedelta(days=days_old)


def random_anniversary(dob):
    days_after_marriage = random.randint(2 * 365, 10 * 365)
    return dob + timedelta(days=22 * 365 + days_after_marriage)


class Command(BaseCommand):
    help = 'Create dummy Sub Dealers — every dealer gets AT LEAST 1, remaining spread randomly (mixed counts)'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='Total number of dummy sub dealers to create')

    def handle(self, *args, **options):
        count = options['count']
        created = 0

        dealers = list(DealerProfile.objects.all())
        if not dealers:
            self.stdout.write(self.style.ERROR("No dealers found! Create dealers first."))
            return

        total_dealers = len(dealers)

        if count < total_dealers:
            self.stdout.write(self.style.ERROR(
                f"count={count} is less than total_dealers={total_dealers}. "
                f"Need count >= number of dealers so every dealer can get at least 1."
            ))
            return

        # ── Build the assignment plan BEFORE creating anything ──
        # Step A: guarantee every dealer gets exactly 1 (no dealer left with 0)
        assignment_plan = list(dealers)  # 1 slot per dealer
        # Step B: remaining slots go to random dealers (this is what makes it "mixed" —
        # some dealers will end up with just 1, others with several extra)
        remaining = count - total_dealers
        for _ in range(remaining):
            assignment_plan.append(random.choice(dealers))

        random.shuffle(assignment_plan)  # so the "guaranteed 1" ones aren't all created first

        self.stdout.write(self.style.SUCCESS(
            f"Found {total_dealers} dealers. Every dealer gets >= 1. "
            f"Creating {count} sub dealers total (mixed distribution)..."
        ))

        dealer_tally = {d.id: 0 for d in dealers}

        for dealer in assignment_plan:
            first_name = random.choice(FIRST_NAMES)
            father_name = random.choice(FATHER_NAMES)
            initial = random.choice(INITIALS)
            city, district, state = random.choice(CITIES)

            mobile = f"9{random.randint(100000000, 999999999)}"
            aadhaar = str(random.randint(100000000000, 999999999999))
            pan = f"SD{random.randint(100000, 999999)}"

            occupation = random.choice(['employee', 'business', 'others'])
            occupation_detail = random.choice(OCCUPATION_DETAILS[occupation])

            dob = random_dob()
            married_status = random.choice(['single', 'married'])
            anniversary_date = random_anniversary(dob) if married_status == 'married' else None

            # ── FIX (same pattern as dealers): email serial number comes from
            # SubDealerProfile.objects.count()+1 — the SAME counter that generates
            # sub_dealer_id (BBSDL{year}{count:07d}). This keeps email and ID
            # numbers consistent, AND naturally continues from the existing 1
            # sub dealer already in the DB (so this run starts at 002, not 001).
            serial_num = SubDealerProfile.objects.count() + 1
            serial = str(serial_num).zfill(2)

            temp_email = f"temp_subdealer_{serial_num}_{random.randint(1000,9999)}@bitbyte.test"
            user = User.objects.create_user(
                email=temp_email,
                password=DUMMY_PASSWORD,
                role='sub_dealer',
            )
            email = f"{first_name.lower()}{serial}@gmail.com"

            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                self.stdout.write(self.style.WARNING(f"Skip: {email} already exists, removing temp user"))
                user.delete()
                continue

            user.email = email
            user.save(update_fields=['email'])

            SubDealerProfile.objects.create(
                user=user,
                created_by=dealer.user,
                assigned_dealer=dealer,
                initial=initial,
                first_name=first_name,
                last_name=father_name,
                mobile_number=mobile,
                gender=random.choice(['male', 'female']),
                dob=dob,
                married_status=married_status,
                anniversary_date=anniversary_date,
                door_no=f"{random.randint(1, 200)}",
                street_name="Main Street",
                town_name=city,
                city_name=city,
                district=district,
                state=state,
                aadhaar_no=aadhaar,
                pan_no=pan,
                occupation=occupation,
                occupation_detail=occupation_detail,
                annual_salary=str(random.randint(120000, 500000)),
            )

            dealer_tally[dealer.id] += 1
            created += 1
            self.stdout.write(self.style.SUCCESS(
                f"Created: {email} / {DUMMY_PASSWORD} -> assigned to Dealer {dealer.dealer_id} ({dealer.first_name})"
            ))

        self.stdout.write(self.style.SUCCESS(f"\nDone! {created} dummy sub dealers created and linked to {total_dealers} dealers."))

        zero_dealers = [d for d in dealers if dealer_tally[d.id] == 0]
        self.stdout.write(self.style.SUCCESS("\n── Distribution summary ──"))
        for d in dealers:
            n = dealer_tally[d.id]
            self.stdout.write(f"  {d.dealer_id} ({d.first_name}) -> {n} sub dealer(s)")
        if zero_dealers:
            self.stdout.write(self.style.ERROR(f"⚠️ {len(zero_dealers)} dealers got 0 (should not happen — check for skipped duplicates)"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Every dealer has at least 1 sub dealer."))