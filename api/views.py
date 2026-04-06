"""
api/views.py
REST API endpoints (Django REST Framework).
Public endpoints for elections, candidates, results.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from voting.models import Election, Position, Candidate, Vote
from .serializers import ElectionSerializer, CandidateSerializer, ResultsSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def elections_list(request):
    """
    GET /api/elections/
    Returns list of all active and upcoming elections.
    """
    now = timezone.now()
    elections = Election.objects.filter(
        end_time__gte=now
    ).order_by('start_time')
    serializer = ElectionSerializer(elections, many=True)
    return Response({
        'count': elections.count(),
        'elections': serializer.data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def candidates_list(request, election_id):
    """
    GET /api/candidates/<election_id>/
    Returns all candidates grouped by position for an election.
    """
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'error': 'Election not found'}, status=404)

    positions_data = []
    for position in election.positions.prefetch_related('candidates').all():
        positions_data.append({
            'position_id': position.id,
            'position': position.title,
            'candidates': CandidateSerializer(position.candidates.all(), many=True).data
        })

    return Response({
        'election_id': election.id,
        'election_name': election.name,
        'positions': positions_data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def election_results(request, election_id):
    """
    GET /api/results/<election_id>/
    Returns published vote results for an election.
    Only returns data if results are published.
    """
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'error': 'Election not found'}, status=404)

    if not election.is_published:
        return Response(
            {'error': 'Results not yet published'},
            status=status.HTTP_403_FORBIDDEN
        )

    results = []
    for position in election.positions.prefetch_related('candidates').all():
        total = sum(c.vote_count for c in position.candidates.all())
        candidates = []
        for candidate in position.candidates.all():
            candidates.append({
                'id': candidate.id,
                'name': candidate.name,
                'votes': candidate.vote_count,
                'percentage': round(candidate.vote_count / total * 100, 1) if total else 0,
            })
        candidates.sort(key=lambda x: x['votes'], reverse=True)
        results.append({
            'position': position.title,
            'total_votes': total,
            'candidates': candidates,
            'winner': candidates[0]['name'] if candidates else None,
        })

    return Response({
        'election_id': election.id,
        'election_name': election.name,
        'is_published': election.is_published,
        'results': results,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_votes(request):
    """
    GET /api/my-votes/
    Returns the authenticated user's voting history.
    """
    votes = Vote.objects.filter(voter=request.user).select_related(
        'election', 'position', 'candidate'
    )
    votes_data = [
        {
            'election': v.election.name,
            'position': v.position.title,
            'candidate': v.candidate.name,
            'timestamp': v.timestamp.isoformat(),
        }
        for v in votes
    ]
    return Response({'votes': votes_data, 'total': len(votes_data)})
