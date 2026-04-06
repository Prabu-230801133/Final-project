"""
web_admin/views.py
Custom admin dashboard views for Web Admin users.
Full CRUD for Elections, Positions, Candidates, and Results.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from voting.models import Election, Position, Candidate, Vote, UserElectionMapping
from accounts.models import CustomUser
from accounts.decorators import web_admin_required


@web_admin_required
def dashboard(request):
    """
    Web Admin dashboard overview.
    Shows stats: total elections, voters, votes cast, active elections.
    """
    now = timezone.now()
    total_elections = Election.objects.count()
    total_voters = CustomUser.objects.filter(role='student').count()
    total_votes = Vote.objects.count()
    active_elections = Election.objects.filter(
        start_time__lte=now, end_time__gte=now
    ).count()

    # Recent elections for quick view
    recent_elections = Election.objects.order_by('-created_at')[:5]

    # Vote activity data for chart (last 7 elections)
    elections_chart = Election.objects.annotate(
        vote_count=Count('votes')
    ).order_by('-created_at')[:7]

    chart_labels = [e.name[:20] for e in elections_chart]
    chart_data = [e.vote_count for e in elections_chart]

    context = {
        'total_elections': total_elections,
        'total_voters': total_voters,
        'total_votes': total_votes,
        'active_elections': active_elections,
        'recent_elections': recent_elections,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'web_admin/dashboard.html', context)


# ──────────────── ELECTION MANAGEMENT ────────────────

@web_admin_required
def elections_list(request):
    """List all elections with status, voter count, vote count."""
    elections = Election.objects.annotate(
        vote_count=Count('votes', distinct=True),
        voter_count=Count('userelectionmapping_set', distinct=True)
    ).order_by('-start_time')
    return render(request, 'web_admin/elections_list.html', {'elections': elections})


@web_admin_required
def election_create(request):
    """Create a new election."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if not all([name, start_time, end_time]):
            messages.error(request, 'Name, start time, and end time are required.')
            return render(request, 'web_admin/election_form.html')

        election = Election.objects.create(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            created_by=request.user,
        )
        messages.success(request, f'Election "{election.name}" created successfully!')
        return redirect('web_admin:election_detail', election_id=election.id)

    return render(request, 'web_admin/election_form.html')


@web_admin_required
def election_detail_admin(request, election_id):
    """Admin view of election detail: manage positions, candidates, voters."""
    election = get_object_or_404(Election, id=election_id)
    positions = election.positions.prefetch_related('candidates').all()
    assigned_users = UserElectionMapping.objects.filter(
        election=election
    ).select_related('user')
    all_students = CustomUser.objects.filter(role='student', is_active=True)

    context = {
        'election': election,
        'positions': positions,
        'assigned_users': assigned_users,
        'all_students': all_students,
    }
    return render(request, 'web_admin/election_detail.html', context)


@web_admin_required
def election_delete(request, election_id):
    """Delete an election (POST)."""
    election = get_object_or_404(Election, id=election_id)
    if request.method == 'POST':
        name = election.name
        election.delete()
        messages.success(request, f'Election "{name}" deleted.')
        return redirect('web_admin:elections_list')
    return render(request, 'web_admin/confirm_delete.html', {
        'object': election, 'type': 'Election'
    })


@web_admin_required
def election_publish(request, election_id):
    """Toggle publish/unpublish results."""
    election = get_object_or_404(Election, id=election_id)
    election.is_published = not election.is_published
    election.save(update_fields=['is_published'])
    status = 'published' if election.is_published else 'unpublished'
    messages.success(request, f'Results {status} for "{election.name}".')
    return redirect('web_admin:election_detail', election_id=election_id)


# ──────────────── POSITION MANAGEMENT ────────────────

@web_admin_required
def position_add(request, election_id):
    """Add a position to an election."""
    election = get_object_or_404(Election, id=election_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        if not title:
            messages.error(request, 'Position title is required.')
        else:
            Position.objects.create(
                election=election, title=title, description=description
            )
            messages.success(request, f'Position "{title}" added.')
    return redirect('web_admin:election_detail', election_id=election_id)


@web_admin_required
def position_delete(request, position_id):
    """Remove a position from an election."""
    position = get_object_or_404(Position, id=position_id)
    election_id = position.election_id
    if request.method == 'POST':
        position.delete()
        messages.success(request, 'Position removed.')
    return redirect('web_admin:election_detail', election_id=election_id)


# ──────────────── CANDIDATE MANAGEMENT ────────────────

@web_admin_required
def candidate_add(request, position_id):
    """Add a candidate to a position (with photo upload to Cloudinary)."""
    position = get_object_or_404(Position, id=position_id)
    election_id = position.election_id

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        bio = request.POST.get('bio', '').strip()
        manifesto = request.POST.get('manifesto', '').strip()
        photo = request.FILES.get('photo')

        if not name:
            messages.error(request, 'Candidate name is required.')
        else:
            candidate = Candidate.objects.create(
                position=position,
                name=name,
                bio=bio,
                manifesto=manifesto,
            )
            # Handle photo upload (Cloudinary or local)
            if photo:
                candidate.photo = photo
                candidate.save(update_fields=['photo'])

            messages.success(request, f'Candidate "{name}" added.')
    return redirect('web_admin:election_detail', election_id=election_id)


@web_admin_required
def candidate_delete(request, candidate_id):
    """Remove a candidate."""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    election_id = candidate.position.election_id
    if request.method == 'POST':
        candidate.delete()
        messages.success(request, 'Candidate removed.')
    return redirect('web_admin:election_detail', election_id=election_id)


# ──────────────── VOTER ASSIGNMENT ────────────────

@web_admin_required
def assign_voter(request, election_id):
    """Assign a student to an election."""
    election = get_object_or_404(Election, id=election_id)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(CustomUser, id=user_id, role='student')
        mapping, created = UserElectionMapping.objects.get_or_create(
            user=user,
            election=election,
            defaults={'assigned_by': request.user}
        )
        if created:
            messages.success(request, f'{user.get_full_name() or user.username} assigned.')
        else:
            messages.info(request, 'Already assigned.')
    return redirect('web_admin:election_detail', election_id=election_id)


@web_admin_required
def remove_voter(request, election_id, user_id):
    """Remove voter assignment."""
    UserElectionMapping.objects.filter(
        election_id=election_id, user_id=user_id
    ).delete()
    messages.success(request, 'Voter removed from election.')
    return redirect('web_admin:election_detail', election_id=election_id)


# ──────────────── LIVE RESULTS ────────────────

@web_admin_required
def live_results(request, election_id):
    """
    Admin live results page.
    Shows real-time vote counts per candidate per position.
    """
    election = get_object_or_404(Election, id=election_id)
    positions = election.positions.prefetch_related('candidates__votes').all()

    positions_data = []
    for position in positions:
        candidates_data = []
        total = sum(c.vote_count for c in position.candidates.all())
        for candidate in position.candidates.all():
            pct = round((candidate.vote_count / total * 100), 1) if total else 0
            candidates_data.append({
                'id': candidate.id,
                'name': candidate.name,
                'photo_url': candidate.photo_url,
                'votes': candidate.vote_count,
                'percentage': pct,
            })
        candidates_data.sort(key=lambda x: x['votes'], reverse=True)
        positions_data.append({
            'position': position,
            'candidates': candidates_data,
            'total': total,
        })

    context = {
        'election': election,
        'positions_data': positions_data,
    }
    return render(request, 'web_admin/live_results.html', context)


@web_admin_required
def live_results_api(request, election_id):
    """JSON endpoint for live results polling (AJAX)."""
    election = get_object_or_404(Election, id=election_id)
    data = {}
    for position in election.positions.prefetch_related('candidates').all():
        total = sum(c.vote_count for c in position.candidates.all())
        data[position.title] = [
            {
                'name': c.name,
                'votes': c.vote_count,
                'percentage': round(c.vote_count / total * 100, 1) if total else 0,
            }
            for c in position.candidates.all()
        ]
    return JsonResponse({'election': election.name, 'results': data})


# ──────────────── STUDENT MANAGEMENT ────────────────

@web_admin_required
def students_list(request):
    """List all registered students."""
    students = CustomUser.objects.filter(role='student').order_by('last_name', 'first_name')
    return render(request, 'web_admin/students_list.html', {'students': students})
