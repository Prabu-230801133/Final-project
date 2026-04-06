"""
voting/views.py
Student-facing views:
- Public homepage (landing page)
- Student dashboard (assigned elections)
- Election detail & vote casting
- Results view
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from accounts.decorators import student_required
from accounts.utils import send_vote_confirmation_email
from .models import Election, Position, Candidate, Vote, UserElectionMapping


def home(request):
    """
    Public landing page.
    Shows active/published elections, candidates, and winners.
    No authentication required.
    """
    now = timezone.now()

    # Active elections visible to public
    active_elections = Election.objects.filter(
        start_time__lte=now,
        end_time__gte=now
    ).prefetch_related('positions__candidates')

    # Published elections (any — admin may publish while still active or after ending)
    published_elections = Election.objects.filter(
        is_published=True
    ).prefetch_related('positions__candidates__votes').order_by('-end_time')

    # Compute winners per position for each published election
    published_results = []
    for election in published_elections:
        winners = []
        for position in election.positions.all():
            candidates = list(position.candidates.all())
            if not candidates:
                continue
            # Pick candidate with most votes (only show if votes exist)
            winner = max(candidates, key=lambda c: c.vote_count)
            if winner.vote_count > 0:
                winners.append({
                    'position': position.title,
                    'winner': winner,
                })
        published_results.append({
            'election': election,
            'winners': winners,
        })

    # Upcoming elections (for countdown timers)
    upcoming_elections = Election.objects.filter(
        start_time__gt=now
    ).order_by('start_time')[:3]

    context = {
        'active_elections': active_elections,
        'published_results': published_results,
        'upcoming_elections': upcoming_elections,
    }
    return render(request, 'voting/home.html', context)



@login_required
def student_dashboard(request):
    """
    Student dashboard: shows elections the student is assigned to.
    Shows vote status for each election.
    """
    user = request.user
    now = timezone.now()

    # Get elections this student is assigned to
    assignments = UserElectionMapping.objects.filter(
        user=user
    ).select_related('election').order_by('-election__start_time')

    elections_data = []
    for assignment in assignments:
        election = assignment.election

        # Check if student has already voted in this election
        voted_positions = Vote.objects.filter(
            voter=user,
            election=election
        ).values_list('position_id', flat=True)

        total_positions = election.positions.count()
        votes_cast = len(voted_positions)
        fully_voted = (votes_cast == total_positions and total_positions > 0)

        elections_data.append({
            'election': election,
            'status': election.status,
            'fully_voted': fully_voted,
            'votes_cast': votes_cast,
            'total_positions': total_positions,
            # True when admin has published results — voting is permanently closed
            'is_results_locked': election.is_published,
        })

    context = {
        'elections_data': elections_data,
        'now': now,
    }
    return render(request, 'voting/student_dashboard.html', context)


@login_required
def election_detail(request, election_id):
    """
    Shows positions and candidates for an election.
    Students can cast votes from this page.
    """
    user = request.user
    now = timezone.now()

    election = get_object_or_404(Election, id=election_id)

    # Verify student is assigned to this election
    if not request.user.is_superuser and user.role == 'student':
        if not UserElectionMapping.objects.filter(user=user, election=election).exists():
            messages.error(request, 'You are not eligible for this election.')
            return redirect('voting:student_dashboard')

    # Get all positions with candidates
    positions = election.positions.prefetch_related('candidates').all()

    # Find which positions this user has already voted in
    voted_positions = set(Vote.objects.filter(
        voter=user, election=election
    ).values_list('position_id', flat=True))

    positions_data = []
    for position in positions:
        positions_data.append({
            'position': position,
            'candidates': position.candidates.all(),
            'already_voted': position.id in voted_positions,
        })

    context = {
        'election': election,
        'positions_data': positions_data,
        # Voting blocked if election not active OR results already published
        'can_vote': election.is_active and not election.is_published,
        'now': now,
    }
    return render(request, 'voting/election_detail.html', context)


@login_required
def cast_vote(request, election_id):
    """
    Process vote submission (POST only).
    Enforces: one vote per student per position per election.
    Sends confirmation email after successful vote.
    """
    if request.method != 'POST':
        return redirect('voting:election_detail', election_id=election_id)

    user = request.user
    election = get_object_or_404(Election, id=election_id)

    # Verify election is active
    if not election.is_active:
        messages.error(request, 'This election is not currently active.')
        return redirect('voting:student_dashboard')

    # Block voting if results have been published
    if election.is_published:
        messages.error(request, f'Results for "{election.name}" have been published. Voting is now closed.')
        return redirect('voting:election_results', election_id=election.id)

    # Verify student assignment
    if user.role == 'student' and not request.user.is_superuser:
        if not UserElectionMapping.objects.filter(user=user, election=election).exists():
            messages.error(request, 'You are not eligible for this election.')
            return redirect('voting:student_dashboard')

    errors = []
    votes_to_create = []

    # Parse votes from form (field name = position_<id>, value = candidate_<id>)
    for key, value in request.POST.items():
        if key.startswith('position_') and value:
            try:
                position_id = int(key.replace('position_', ''))
                candidate_id = int(value.replace('candidate_', ''))

                position = get_object_or_404(Position, id=position_id, election=election)
                candidate = get_object_or_404(Candidate, id=candidate_id, position=position)

                # Check if already voted for this position
                if Vote.objects.filter(voter=user, election=election, position=position).exists():
                    errors.append(f'Already voted for {position.title}.')
                    continue

                votes_to_create.append(Vote(
                    voter=user,
                    candidate=candidate,
                    election=election,
                    position=position,
                ))
            except (ValueError, TypeError):
                errors.append(f'Invalid vote data for {key}')

    if errors:
        for err in errors:
            messages.warning(request, err)

    if votes_to_create:
        # Bulk create all votes atomically
        Vote.objects.bulk_create(votes_to_create)

        # Send confirmation email (non-blocking on failure)
        try:
            send_vote_confirmation_email(user, election)
        except Exception:
            pass  # Email failure should not block vote confirmation

        messages.success(
            request,
            f'✅ Your vote has been successfully cast in "{election.name}"!'
        )

    return redirect('voting:vote_success', election_id=election_id)


@login_required
def vote_success(request, election_id):
    """Thank-you page after voting."""
    election = get_object_or_404(Election, id=election_id)
    return render(request, 'voting/vote_success.html', {'election': election})


def election_results(request, election_id):
    """
    Public results page for published elections.
    Shows vote counts per candidate per position.
    """
    election = get_object_or_404(Election, id=election_id)

    # Only show results if published or user is admin
    if not election.is_published and not (
        request.user.is_authenticated and
        (request.user.is_superuser or request.user.role in ['web_admin', 'django_admin'])
    ):
        messages.info(request, 'Results have not been published yet.')
        return redirect('home')

    positions = election.positions.prefetch_related(
        'candidates__votes'
    ).all()

    positions_data = []
    for position in positions:
        candidates_data = []
        total_votes = sum(c.vote_count for c in position.candidates.all())
        for candidate in position.candidates.all():
            pct = round((candidate.vote_count / total_votes * 100), 1) if total_votes > 0 else 0
            candidates_data.append({
                'candidate': candidate,
                'votes': candidate.vote_count,
                'percentage': pct,
            })
        # Sort by votes descending
        candidates_data.sort(key=lambda x: x['votes'], reverse=True)
        positions_data.append({
            'position': position,
            'candidates': candidates_data,
            'total_votes': total_votes,
        })

    context = {
        'election': election,
        'positions_data': positions_data,
    }
    return render(request, 'voting/results.html', context)
