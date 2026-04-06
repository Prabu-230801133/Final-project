"""
seed_data.py — Populate the database with sample data for testing.
Run with: python seed_data.py
Or: python manage.py shell < seed_data.py
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.hashers import make_password
from datetime import timedelta

from accounts.models import CustomUser
from voting.models import Election, Position, Candidate, UserElectionMapping


def create_seed_data():
    print("🌱 Seeding database...")

    # ── 1. Create superuser (Django Admin) ──
    if not CustomUser.objects.filter(username='admin').exists():
        admin = CustomUser.objects.create(
            username='admin',
            email='admin@college.edu',
            first_name='Super',
            last_name='Admin',
            role='django_admin',
            is_staff=True,
            is_superuser=True,
            password=make_password('Admin@123'),
        )
        print(f"  ✅ Created Django admin: admin / Admin@123")
    else:
        admin = CustomUser.objects.get(username='admin')
        print(f"  ⏭️  Django admin already exists")

    # ── 2. Create Web Admin ──
    if not CustomUser.objects.filter(username='webadmin').exists():
        webadmin = CustomUser.objects.create(
            username='webadmin',
            email='webadmin@college.edu',
            first_name='Web',
            last_name='Admin',
            role='web_admin',
            is_staff=False,
            password=make_password('WebAdmin@123'),
        )
        print(f"  ✅ Created Web Admin: webadmin / WebAdmin@123")
    else:
        webadmin = CustomUser.objects.get(username='webadmin')
        print(f"  ⏭️  Web admin already exists")

    # ── 3. Create sample students ──
    students_data = [
        {'username': 'student1', 'first_name': 'Arjun', 'last_name': 'Kumar', 'student_id': 'CS2023001', 'dept': 'Computer Science'},
        {'username': 'student2', 'first_name': 'Priya', 'last_name': 'Sharma', 'student_id': 'EC2023002', 'dept': 'Electronics'},
        {'username': 'student3', 'first_name': 'Rahul', 'last_name': 'Verma', 'student_id': 'ME2023003', 'dept': 'Mechanical'},
        {'username': 'student4', 'first_name': 'Sneha', 'last_name': 'Reddy', 'student_id': 'CS2023004', 'dept': 'Computer Science'},
        {'username': 'student5', 'first_name': 'Kiran', 'last_name': 'Patel', 'student_id': 'CI2023005', 'dept': 'Civil Engineering'},
    ]

    students = []
    for s in students_data:
        if not CustomUser.objects.filter(username=s['username']).exists():
            student = CustomUser.objects.create(
                username=s['username'],
                email=f"{s['username']}@college.edu",
                first_name=s['first_name'],
                last_name=s['last_name'],
                role='student',
                student_id=s['student_id'],
                department=s['dept'],
                credentials_sent=True,
                password=make_password('Student@123'),
            )
            students.append(student)
            print(f"  ✅ Created student: {s['username']} / Student@123")
        else:
            students.append(CustomUser.objects.get(username=s['username']))
            print(f"  ⏭️  Student {s['username']} already exists")

    # ── 4. Create Elections ──
    now = timezone.now()

    # Active election
    election1, e1_created = Election.objects.get_or_create(
        name="Student Council Election 2025",
        defaults={
            'description': 'Annual election for Student Council. All students are encouraged to vote!',
            'start_time': now - timedelta(hours=2),
            'end_time': now + timedelta(days=2),
            'created_by': admin,
        }
    )
    print(f"  {'✅ Created' if e1_created else '⏭️  Exists'}: {election1.name}")

    # Upcoming election
    election2, e2_created = Election.objects.get_or_create(
        name="Sports Committee Election 2025",
        defaults={
            'description': 'Elect your Sports Committee representatives for the upcoming year.',
            'start_time': now + timedelta(days=5),
            'end_time': now + timedelta(days=8),
            'created_by': admin,
        }
    )
    print(f"  {'✅ Created' if e2_created else '⏭️  Exists'}: {election2.name}")

    # ── 5. Add Positions to Election 1 ──
    president_pos, _ = Position.objects.get_or_create(
        election=election1, title="President",
        defaults={'description': 'Head of the Student Council', 'order': 1}
    )
    secretary_pos, _ = Position.objects.get_or_create(
        election=election1, title="Secretary",
        defaults={'description': 'Secretary of the Student Council', 'order': 2}
    )
    treasurer_pos, _ = Position.objects.get_or_create(
        election=election1, title="Treasurer",
        defaults={'description': 'Manages student council funds', 'order': 3}
    )

    # ── 6. Add Candidates ──
    candidates_data = [
        # President candidates
        {'position': president_pos, 'name': 'Aditya Nair', 'bio': 'Passionate about student welfare and campus development.'},
        {'position': president_pos, 'name': 'Divya Menon', 'bio': '3 years of leadership experience in college clubs.'},
        # Secretary candidates
        {'position': secretary_pos, 'name': 'Rohan Singh', 'bio': 'Detail-oriented with strong organizational skills.'},
        {'position': secretary_pos, 'name': 'Anjali Bose', 'bio': 'Committed to transparent governance and student rights.'},
        # Treasurer candidates
        {'position': treasurer_pos, 'name': 'Vikram Rao', 'bio': 'Finance student with budgeting experience.'},
        {'position': treasurer_pos, 'name': 'Meena Das', 'bio': 'Accountable and transparent with financial matters.'},
    ]

    for cd in candidates_data:
        Candidate.objects.get_or_create(
            position=cd['position'],
            name=cd['name'],
            defaults={'bio': cd['bio']}
        )
    print(f"  ✅ Candidates added for {election1.name}")

    # ── 7. Assign students to election ──
    for student in students:
        UserElectionMapping.objects.get_or_create(
            user=student,
            election=election1,
            defaults={'assigned_by': admin}
        )
    print(f"  ✅ Assigned {len(students)} students to {election1.name}")

    # ── 8. Add positions to election 2 ──
    sports_pos, _ = Position.objects.get_or_create(
        election=election2, title="Sports Captain",
        defaults={'order': 1}
    )
    Candidate.objects.get_or_create(
        position=sports_pos, name="Mohan Iyer",
        defaults={'bio': 'National-level athlete with team leadership skills.'}
    )
    Candidate.objects.get_or_create(
        position=sports_pos, name="Fatima Hussain",
        defaults={'bio': 'College sports champion 2024.'}
    )

    print("\n🎉 Seed data complete!")
    print("\n📋 Login Credentials:")
    print("  🔧 Django Admin  : http://localhost:8000/django-admin/  →  admin / Admin@123")
    print("  ⚙️  Web Admin     : http://localhost:8000/admin-dashboard/  →  webadmin / WebAdmin@123")
    print("  🎓 Students      : http://localhost:8000/accounts/login/  →  student1-5 / Student@123")


if __name__ == '__main__':
    create_seed_data()
