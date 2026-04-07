"""
accounts/utils.py
Email utility functions for the voting system.
"""
from django.core.mail import send_mail
from django.conf import settings


def send_credentials_email(user, plain_password):
    """
    Send login credentials to a newly created student.
    Called from Django admin action after generating username/password.
    """
    subject = "Your College Voting System Login Credentials"
    message = f"""
Dear {user.get_full_name() or user.username},

Your account has been created on the College Voting System.

Login Details:
--------------
Username : {user.username}
Password : {plain_password}

Login at: http://localhost:8000/accounts/login/

Please change your password after first login.

If you did not request this account, please contact the administration.

Best regards,
College Election Committee
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_vote_confirmation_email(user, election):
    """
    Send confirmation email after a student successfully votes.
    Called from voting/views.py after a vote is recorded.
    """
    subject = f"Vote Confirmation - {election.name}"
    message = f"""
Dear {user.get_full_name() or user.username},

You have successfully cast your vote in {election.name}.

Election Details:
----------------
Election : {election.name}
Voted at : {election.start_time.strftime('%d %B %Y')}

Your vote has been recorded securely. Thank you for participating!

Results will be published after the election ends on {election.end_time.strftime('%d %B %Y, %I:%M %p')}.

Best regards,
College Election Committee
    """.strip()

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_election_scheduled_email(users, election):
    """
    Send notification to all assigned students when an election is scheduled.
    users: queryset or list of CustomUser objects.
    """
    subject = f"Election Announcement: {election.name}"
    for user in users:
        if not user.email:
            continue
        message = f"""
Dear {user.get_full_name() or user.username},

You have been registered to vote in the upcoming election!

Election Details:
-----------------
Election  : {election.name}
Starts    : {election.start_time.strftime('%d %B %Y, %I:%M %p')}
Ends      : {election.end_time.strftime('%d %B %Y, %I:%M %p')}
Description: {election.description or 'N/A'}

Please log in on time to cast your vote.
Login: http://localhost:8000/accounts/login/

Best regards,
College Election Committee
        """.strip()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


def send_voting_reminder_email(users, election):
    """
    Send a gentle reminder email to voters 2 hours before voting opens.
    """
    subject = f"Reminder: Voting Opens Soon - {election.name}"
    for user in users:
        if not user.email:
            continue
        message = f"""
Dear {user.get_full_name() or user.username},

This is a gentle reminder that voting for "{election.name}" opens in less than 2 hours!

Election Details:
-----------------
Election  : {election.name}
Opens at  : {election.start_time.strftime('%d %B %Y, %I:%M %p')}
Closes at : {election.end_time.strftime('%d %B %Y, %I:%M %p')}

Please make sure to cast your vote on time. Every vote counts!
Login: http://localhost:8000/accounts/login/

Best regards,
College Election Committee
        """.strip()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
