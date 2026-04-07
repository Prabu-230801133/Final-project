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

    # ── 4. Delete Old Elections & Create New Ones ──
    now = timezone.now()
    
    print("  🗑️ Deleting existing elections...")
    Election.objects.all().delete()

    elections_data = [
        {
            'name': "Student Council Election",
            'description': 'Annual election for Student Council.',
            'start_time': now - timedelta(hours=2),
            'end_time': now + timedelta(days=2),
            'positions': [("President", "Head of the Student Council", 1), ("Secretary", "Secretary of the Student Council", 2)]
        },
        {
            'name': "Sports Committee Election",
            'description': 'Elect your Sports Committee representatives.',
            'start_time': now + timedelta(days=5),
            'end_time': now + timedelta(days=8),
            'positions': [("Sports Captain", "Head of the Sports Committee", 1)]
        },
        {
            'name': "Hostel Committee Election",
            'description': 'Election for hostel representatives.',
            'start_time': now + timedelta(days=1),
            'end_time': now + timedelta(days=3),
            'positions': [("Hostel Secretary", "Representative of hostel affairs", 1)]
        },
        {
            'name': "Recharge Core Team Election",
            'description': 'Election to select the core team for Recharge.',
            'start_time': now + timedelta(days=10),
            'end_time': now + timedelta(days=15),
            'positions': [("Core Member", "Member of the Recharge Core Team", 1)]
        },
        {
            'name': "Class Election for Monitor and Vice Monitor",
            'description': 'Select your class monitor and vice monitor.',
            'start_time': now - timedelta(days=1),
            'end_time': now + timedelta(days=1),
            'positions': [("Monitor", "Class Monitor", 1), ("Vice Monitor", "Class Vice Monitor", 2)]
        }
    ]

    for edata in elections_data:
        election = Election.objects.create(
            name=edata['name'],
            description=edata['description'],
            start_time=edata['start_time'],
            end_time=edata['end_time'],
            created_by=admin,
            is_published=True
        )
        print(f"  ✅ Created Election: {election.name}")

        for p_title, p_desc, p_order in edata['positions']:
            pos = Position.objects.create(
                election=election, title=p_title, description=p_desc, order=p_order
            )
            # Create a couple of dummy candidates for each position
            Candidate.objects.create(position=pos, name=f"Candidate A for {p_title}")
            Candidate.objects.create(position=pos, name=f"Candidate B for {p_title}")

        # Assign all students to all these elections
        for student in students:
            UserElectionMapping.objects.get_or_create(
                user=student,
                election=election,
                defaults={'assigned_by': admin}
            )

    print("\n🎉 Seed data complete!")
    print("\n📋 Login Credentials:")
    print("  🔧 Django Admin  : http://localhost:8000/django-admin/  →  admin / Admin@123")
    print("  ⚙️  Web Admin     : http://localhost:8000/admin-dashboard/  →  webadmin / WebAdmin@123")
    print("  🎓 Students      : http://localhost:8000/accounts/login/  →  student1-5 / Student@123")


if __name__ == '__main__':
    create_seed_data()
