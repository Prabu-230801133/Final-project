"""
accounts/models.py
Custom user model with role-based access control.
Roles: 'django_admin', 'web_admin', 'student'
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Extended user model with college-specific fields."""

    ROLE_CHOICES = [
        ('django_admin', 'Django Admin'),
        ('web_admin', 'Web Admin'),
        ('student', 'Student'),
    ]

    # Role field determines dashboard redirect
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        help_text='User role determines access level'
    )

    # Student-specific fields
    student_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text='Student registration number'
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    # Tracks if user received their generated credentials
    credentials_sent = models.BooleanField(default=False)

    # Raw password stored temporarily for email sending (cleared after send)
    _plain_password = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_web_admin(self):
        return self.role == 'web_admin'

    @property
    def is_django_admin(self):
        return self.role == 'django_admin'
