"""
voting/views.py
Student-facing views:
- Public homepage (landing page)
- Student dashboard (assigned elections)
- Election detail & vote casting
- Post-vote feedback form
- Results view
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg
from accounts.decorators import student_required
from accounts.utils import send_vote_confirmation_email
from .models import Election, Position, Candidate, Vote, UserElectionMapping, VoteFeedback, TieBreaker


def home(request):
    """
    Public landing page.
    Shows active/published elections, candidates, and winners.
    No authentication required.
    """
    now = timezone.now()

    active_elections = Election.objects.filter(
        start_time__lte=now,
        end_time__gte=now
    ).prefetch_related('positions__candidates')

    published_elections = Election.objects.filter(
        is_published=True
    ).prefetch_related('positions__candidates__votes').order_by('-end_time')

    published_results = []
    for election in published_elections:
        winners = []
        for position in election.positions.all():
            candidates = list(position.candidates.all())
            if not candidates:
                continue
            # Check for admin-decided tie-break first
            tiebreaker = TieBreaker.objects.filter(
                election=election, position=position
            ).select_related('winner').first()
            if tiebreaker:
                winners.append({
                    'position': position.title,
                    'winner': tiebreaker.winner,
                    'is_tiebreak': True,
                })
            else:
                winner = max(candidates, key=lambda c: c.vote_count)
                if winner.vote_count > 0:
                    winners.append({
                        'position': position.title,
                        'winner': winner,
                        'is_tiebreak': False,
                    })
        published_results.append({
            'election': election,
            'winners': winners,
        })

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

    assignments = UserElectionMapping.objects.filter(
        user=user
    ).select_related('election').order_by('-election__start_time')

    elections_data = []
    for assignment in assignments:
        election = assignment.election

        voted_positions = Vote.objects.filter(
            voter=user,
            election=election
        ).values_list('position_id', flat=True)

        total_positions = election.positions.count()
        votes_cast = len(voted_positions)
        fully_voted = (votes_cast == total_positions and total_positions > 0)

        # Check if feedback was submitted
        has_feedback = VoteFeedback.objects.filter(voter=user, election=election).exists()

        elections_data.append({
            'election': election,
            'status': election.status,
            'fully_voted': fully_voted,
            'votes_cast': votes_cast,
            'total_positions': total_positions,
            'is_results_locked': election.is_published,
            'has_feedback': has_feedback,
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

    if not request.user.is_superuser and user.role == 'student':
        if not UserElectionMapping.objects.filter(user=user, election=election).exists():
            messages.error(request, 'You are not eligible for this election.')
            return redirect('voting:student_dashboard')

    positions = election.positions.prefetch_related('candidates').all()

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
        'can_vote': election.is_active and not election.is_published,
        'now': now,
    }
    return render(request, 'voting/election_detail.html', context)


@login_required
def cast_vote(request, election_id):
    """
    Process vote submission (POST only).
    Enforces: one vote per student per position per election.
    After successful vote, redirects to feedback form.
    """
    if request.method != 'POST':
        return redirect('voting:election_detail', election_id=election_id)

    user = request.user
    election = get_object_or_404(Election, id=election_id)

    if not election.is_active:
        messages.error(request, 'This election is not currently active.')
        return redirect('voting:student_dashboard')

    if election.is_published:
        messages.error(request, f'Results for "{election.name}" have been published. Voting is now closed.')
        return redirect('voting:election_results', election_id=election.id)

    if user.role == 'student' and not request.user.is_superuser:
        if not UserElectionMapping.objects.filter(user=user, election=election).exists():
            messages.error(request, 'You are not eligible for this election.')
            return redirect('voting:student_dashboard')

    errors = []
    chosen_candidate_ids = []

    for key, value in request.POST.items():
        if key.startswith('position_') and value:
            try:
                position_id = int(key.replace('position_', ''))
                candidate_id = int(value.replace('candidate_', ''))

                position = get_object_or_404(Position, id=position_id, election=election)
                candidate = get_object_or_404(Candidate, id=candidate_id, position=position)

                if Vote.objects.filter(voter=user, election=election, position=position).exists():
                    errors.append(f'Already voted for {position.title}.')
                    continue

                chosen_candidate_ids.append(candidate_id)
            except (ValueError, TypeError):
                errors.append(f'Invalid vote data for {key}')

    if errors:
        for err in errors:
            messages.warning(request, err)

    if not chosen_candidate_ids:
        # If no votes were valid, redirect back
        return redirect('voting:election_detail', election_id=election_id)

    import random
    from django.core.mail import send_mail
    from django.conf import settings

    otp = str(random.randint(100000, 999999))
    request.session['vote_otp'] = otp
    request.session['pending_candidates'] = chosen_candidate_ids
    request.session['vote_election_id'] = election_id
    
    try:
        send_mail(
            subject='VoteX - Your Voting OTP',
            message=f'Hello {user.get_full_name() or user.username},\n\nYour OTP to verify and submit your vote is: {otp}\n\nDo not share this code with anyone.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        messages.error(request, 'Failed to send OTP to your email. Please check your account email address.')
        return redirect('voting:election_detail', election_id=election_id)

    messages.info(request, f'An OTP has been sent to {user.email}. Please verify to confirm your vote.')
    return redirect('voting:verify_vote_otp', election_id=election_id)


@login_required
def verify_vote_otp(request, election_id):
    """
    Verify OTP sent to user before finalizing vote submission.
    """
    election = get_object_or_404(Election, id=election_id)
    user = request.user
    
    expected_otp = request.session.get('vote_otp')
    pending_candidates = request.session.get('pending_candidates')
    session_election_id = request.session.get('vote_election_id')
    
    if not pending_candidates or session_election_id != election_id:
        messages.error(request, 'No pending vote found or session expired. Please re-cast your vote.')
        return redirect('voting:election_detail', election_id=election_id)
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        if entered_otp == expected_otp:
            # Success: save the votes
            votes_to_create = []
            for cid in pending_candidates:
                try:
                    candidate = Candidate.objects.get(id=cid)
                    votes_to_create.append(Vote(
                        voter=user,
                        candidate=candidate,
                        election=election,
                        position=candidate.position
                    ))
                except Candidate.DoesNotExist:
                    continue
            
            if votes_to_create:
                Vote.objects.bulk_create(votes_to_create)
                try:
                    send_vote_confirmation_email(user, election)
                except Exception:
                    pass
                messages.success(request, f'Your vote has been successfully cast in "{election.name}"!')
            
            # Clear session
            del request.session['vote_otp']
            del request.session['pending_candidates']
            del request.session['vote_election_id']
            
            return redirect('voting:vote_feedback', election_id=election_id)
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'voting/verify_otp.html', {'election': election})



@login_required
def vote_feedback(request, election_id):
    """
    Post-vote feedback form. Shown after casting a vote.
    Saves VoteFeedback and then redirects to the success page.
    """
    election = get_object_or_404(Election, id=election_id)
    user = request.user

    # If feedback already submitted, go straight to success
    if VoteFeedback.objects.filter(voter=user, election=election).exists():
        return redirect('voting:vote_success', election_id=election_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        experience = request.POST.get('experience')
        comments = request.POST.get('comments', '').strip()

        if not rating or not experience:
            messages.error(request, 'Please provide a rating and experience.')
        else:
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    raise ValueError
            except (ValueError, TypeError):
                messages.error(request, 'Invalid rating value.')
                return render(request, 'voting/vote_feedback.html', {'election': election})

            VoteFeedback.objects.get_or_create(
                voter=user,
                election=election,
                defaults={
                    'rating': rating,
                    'experience': experience,
                    'comments': comments,
                }
            )
            return redirect('voting:vote_success', election_id=election_id)

    return render(request, 'voting/vote_feedback.html', {'election': election})


@login_required
def vote_success(request, election_id):
    """Thank-you page after voting and feedback."""
    election = get_object_or_404(Election, id=election_id)
    return render(request, 'voting/vote_success.html', {'election': election})


def election_results(request, election_id):
    """
    Public results page for published elections.
    Shows vote counts per candidate per position.
    Respects admin tie-break decisions.
    """
    election = get_object_or_404(Election, id=election_id)

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

        # Check for admin tie-break decision
        tiebreaker = TieBreaker.objects.filter(
            election=election, position=position
        ).select_related('winner').first()

        for candidate in position.candidates.all():
            pct = round((candidate.vote_count / total_votes * 100), 1) if total_votes > 0 else 0
            candidates_data.append({
                'candidate': candidate,
                'votes': candidate.vote_count,
                'percentage': pct,
                'is_tiebreak_winner': tiebreaker and tiebreaker.winner_id == candidate.id,
            })
        candidates_data.sort(key=lambda x: x['votes'], reverse=True)
        positions_data.append({
            'position': position,
            'candidates': candidates_data,
            'total_votes': total_votes,
            'tiebreaker': tiebreaker,
        })

    context = {
        'election': election,
        'positions_data': positions_data,
    }
    return render(request, 'voting/results.html', context)
