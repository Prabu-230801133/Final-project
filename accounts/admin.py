"""
accounts/admin.py
Customized Django Admin with:
- Auto-generate username/password for students
- Send login credentials via email (bulk action)
- Assign students to elections inline
"""
import secrets
import string
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django.utils.html import format_html
from .models import CustomUser
from .utils import send_credentials_email
from voting.models import UserElectionMapping


class UserElectionMappingInline(admin.TabularInline):
    """Inline editor to assign/remove user from elections."""
    model = UserElectionMapping
    fk_name = 'user'
    extra = 1
    fields = ['election', 'assigned_at']
    readonly_fields = ['assigned_at']
    verbose_name = "Election Assignment"
    verbose_name_plural = "Election Assignments"


def generate_password(length=10):
    """Generate a random secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_username(first_name, last_name, student_id=None):
    """Generate username from name or student ID."""
    if student_id:
        return f"stu_{student_id.lower()}"
    base = f"{first_name.lower()[:3]}{last_name.lower()[:3]}"
    return base + secrets.token_hex(2)


@admin.action(description="🔑 Generate credentials & send login email")
def send_credentials_action(modeladmin, request, queryset):
    """
    Bulk action: auto-generate username/password for selected users,
    save them, and email the credentials.
    """
    sent = 0
    for user in queryset:
        if user.role != 'student':
            continue

        plain_password = generate_password()

        # Only generate username if not already set meaningfully
        if not user.username or user.username.startswith('stu_'):
            user.username = generate_username(
                user.first_name or 'user',
                user.last_name or 'student',
                user.student_id
            )

        # Hash and save the password
        user.password = make_password(plain_password)
        user.save()

        # Attempt to email credentials
        try:
            send_credentials_email(user, plain_password)
            user.credentials_sent = True
            user.save(update_fields=['credentials_sent'])
            sent += 1
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Failed to send email to {user.email}: {e}",
                level='warning'
            )

    modeladmin.message_user(
        request,
        f"✅ Sent credentials to {sent} student(s)."
    )


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Enhanced UserAdmin with role and election management."""

    list_display = [
        'username', 'email', 'get_full_name', 'role',
        'student_id', 'department', 'credentials_sent', 'is_active'
    ]
    list_filter = ['role', 'credentials_sent', 'is_active', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'student_id']
    actions = [send_credentials_action]

    # Add role, student info to the default UserAdmin fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('College Info', {
            'fields': ('role', 'student_id', 'department', 'phone', 'profile_picture')
        }),
        ('System', {
            'fields': ('credentials_sent',)
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('College Info', {
            'fields': ('email', 'first_name', 'last_name', 'role', 'student_id', 'department', 'phone')
        }),
    )

    # Inline to manage election assignments directly from user page
    inlines = [UserElectionMappingInline]

    def save_model(self, request, obj, form, change):
        """
        Auto-generate credentials and send email when a NEW student is added
        with an email address. Runs after Django's built-in UserAdmin save.
        """
        is_new = obj.pk is None  # True only on creation, not on edit

        # Auto-generate username for new students if blank
        if is_new and obj.role == 'student' and not obj.username:
            obj.username = generate_username(
                obj.first_name or 'user',
                obj.last_name or 'student',
                obj.student_id,
            )

        # Let Django's UserAdmin handle the normal save
        # (it may set a password from the form's password1/password2 fields)
        super().save_model(request, obj, form, change)

        # Now, for new students: overwrite the password with our own generated one
        # so we have the plain-text value to email
        if is_new and obj.role == 'student' and obj.email:
            plain_password = generate_password()
            obj.password = make_password(plain_password)
            obj.save(update_fields=['password'])

            try:
                send_credentials_email(obj, plain_password)
                obj.credentials_sent = True
                obj.save(update_fields=['credentials_sent'])
                messages.success(
                    request,
                    f'✅ Credentials emailed to {obj.email} for user "{obj.username}".'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'⚠️ User created but email failed to send to {obj.email}: {e}'
                )

    def credentials_sent_display(self, obj):
        if obj.credentials_sent:
            return format_html('<span style="color:green">✓ Sent</span>')
        return format_html('<span style="color:red">✗ Not sent</span>')
    credentials_sent_display.short_description = 'Credentials'
