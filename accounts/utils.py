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

Your Login Credentials:
-----------------------
Username : {user.username}
Password : [Your registered password]

If you have forgotten your password, please use the "Forgot Password" link on the login page:
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


def send_vote_otp_email(user, election, otp):
    """
    Send an OTP to the user for verifying their vote.
    """
    if not user.email:
        return False
        
    subject = f"Vote Verification OTP - {election.name}"
    message = f"""
Dear {user.get_full_name() or user.username},

You are attempting to cast your vote in "{election.name}".

Your OTP code is: {otp}

Please enter this code to verify and submit your vote. Do not share this code with anyone.

Best regards,
College Election Committee
    """.strip()

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


def send_results_published_email(users, election):
    """
    Send an email notifying students that election results have been published.
    """
    subject = f"Results Published: {election.name}"
    for user in users:
        if not user.email:
            continue
        message = f"""
Dear {user.get_full_name() or user.username},

The results for "{election.name}" have just been made public!

You can now log in to the portal and view the detailed outcome of the election, including candidate vote counts and percentages.

View Results: http://localhost:8000/voting/results/{election.id}/

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


def send_password_reset_otp_email(user, otp):
    """
    Send an OTP to the user for resetting their password.
    """
    if not user.email:
        return False
        
    subject = "Password Reset Request - VoteX"
    message = f"""
Dear {user.get_full_name() or user.username},

You have requested to reset your password for the College Voting System (VoteX).

Your Password Reset OTP is: {otp}

This code is valid for 10 minutes. If you did not request this, please ignore this email and ensure your account is secure.

Best regards,
College Election Committee
    """.strip()

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False
