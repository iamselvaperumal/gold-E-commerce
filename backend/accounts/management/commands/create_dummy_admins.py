import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from accounts.models import User, AdminProfile


FIRST_NAMES = [
    'Arun', 'Karthik', 'Vignesh', 'Prakash', 'Suresh', 'Ramesh', 'Vijay',
    'Senthil', 'Mani', 'Rajesh', 'Ganesh', 'Anand', 'Bala', 'Dinesh',
    'Elango', 'Gopal', 'Hari', 'Ilango', 'Jagan', 'Kannan', 'Loganathan',
    'Muthu', 'Naveen', 'Prasanna', 'Raja', 'Saravanan',
    'Tamil', 'Uday', 'Vasanth', 'Selvam',
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
]

INITIALS = ['S', 'K', 'M', 'A', 'R', 'V', 'P', 'G', 'D', 'T']

OCCUPATION_DETAILS = {
    'employee': ['Software Engineer', 'Sales Executive', 'Accountant', 'Manager'],
    'business': ['Textile Shop', 'Jewellery Trader', 'Wholesale Merchant'],
    'others': ['Retired', 'Freelancer', 'Self Employed'],
}

DUMMY_PASSWORD = "Senthil@2026"


def random_dob():
    days_old = random.randint(25 * 365, 50 * 365)
    return date.today() - timedelta(days=days_old)


def random_anniversary(dob):
    days_after_marriage = random.randint(3 * 365, 15 * 365)
    return dob + timedelta(days=25 * 365 + days_after_marriage)


class Command(BaseCommand):
    help = 'Create dummy Admin users for testing (all fields filled)'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=30, help='Number of dummy admins to create')

    def handle(self, *args, **options):
        count = options['count']
        created = 0

        for i in range(1, count + 1):
            first_name = random.choice(FIRST_NAMES)
            father_name = random.choice(FATHER_NAMES)
            initial = random.choice(INITIALS)
            city, district, state = random.choice(CITIES)

            temp_email = f"temp_{i}_{random.randint(1000,9999)}@bitbyte.test"

            mobile = f"9{random.randint(100000000, 999999999)}"
            aadhaar = str(random.randint(100000000000, 999999999999))
            pan = f"DUM{random.randint(1000, 9999)}P{i}"

            occupation = random.choice(['employee', 'business', 'others'])
            occupation_detail = random.choice(OCCUPATION_DETAILS[occupation])

            dob = random_dob()
            married_status = random.choice(['single', 'married'])
            anniversary_date = random_anniversary(dob) if married_status == 'married' else None

            # Step 1: temp email vachi user create pannu (user_id auto-generate aagum ippo)
            user = User.objects.create_user(
                email=temp_email,
                password=DUMMY_PASSWORD,
                role='admin',
            )

           # Step 2: Django auto id vachi 3-digit serial build pannu (e.g. 7 -> "007")
            serial = str(user.id).zfill(3)
            email = f"{first_name.lower()}{serial}@gmail.com"

            # Step 3: duplicate check pannu, already irundha temp user delete pannitu skip pannu
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                self.stdout.write(self.style.WARNING(f"Skip: {email} already exists, removing temp user"))
                user.delete()
                continue

            # Step 4: real email set pannu
            user.email = email
            user.save(update_fields=['email'])

            AdminProfile.objects.create(
                user=user,
                created_by=None,
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
                annual_salary=str(random.randint(200000, 900000)),
            )

            created += 1
            self.stdout.write(self.style.SUCCESS(f"Created: {email} / {DUMMY_PASSWORD}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone! {created} dummy admins created successfully."))