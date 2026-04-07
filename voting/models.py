"""
voting/models.py
Core election, candidate, vote models.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Election(models.Model):
    """Represents a college election event."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_published = models.BooleanField(
        default=False,
        help_text='Publish results to public homepage'
    )
    reminder_sent = models.BooleanField(
        default=False,
        help_text='Whether the 2-hour reminder email has been sent'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_elections'
    )

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return self.name

    @property
    def status(self):
        """Computed status based on current time."""
        now = timezone.now()
        if now < self.start_time:
            return 'scheduled'
        elif self.start_time <= now <= self.end_time:
            return 'active'
        else:
            return 'ended'

    @property
    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    @property
    def total_votes(self):
        return Vote.objects.filter(election=self).count()

    @property
    def eligible_voters_count(self):
        return self.userelectionmapping_set.count()


class Position(models.Model):
    """A position within an election (e.g., President, Secretary)."""
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='positions'
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']
        unique_together = ['election', 'title']

    def __str__(self):
        return f"{self.title} — {self.election.name}"


class Candidate(models.Model):
    """A candidate running for a position in an election."""
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='candidates'
    )
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to='candidates/',
        blank=True,
        null=True
    )
    manifesto = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} for {self.position.title}"

    @property
    def vote_count(self):
        return self.votes.count()

    @property
    def photo_url(self):
        """Returns photo URL or a placeholder."""
        if self.photo:
            return self.photo.url
        return '/static/img/default_candidate.png'


class Vote(models.Model):
    """
    A single vote cast by a student.
    unique_together ensures one vote per student per election.
    """
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votes_cast'
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('voter', 'election', 'position')]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.voter.username} voted for {self.candidate.name}"


class UserElectionMapping(models.Model):
    """
    Maps which students are eligible to vote in which elections.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='election_assignments'
    )
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='userelectionmapping_set'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_made'
    )

    class Meta:
        unique_together = [('user', 'election')]
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.user.username} -> {self.election.name}"


class VoteFeedback(models.Model):
    """
    Post-vote feedback submitted by a student after casting their vote.
    One feedback entry per student per election.
    """
    EXPERIENCE_CHOICES = [
        ('smooth', 'Very Smooth'),
        ('neutral', 'Neutral'),
        ('problematic', 'Had Issues'),
    ]
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vote_feedbacks'
    )
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES)
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('voter', 'election')]
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.voter.username} feedback for {self.election.name} — {self.rating}*"


class TieBreaker(models.Model):
    """
    Admin-decided winner when two or more candidates are tied in a position.
    """
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='tiebreakers'
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='tiebreakers'
    )
    winner = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='tiebreaker_wins'
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tiebreaker_decisions'
    )
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('election', 'position')]

    def __str__(self):
        return f"Tie-break: {self.winner.name} wins {self.position.title} in {self.election.name}"
