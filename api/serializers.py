"""
api/serializers.py
DRF serializers for the REST API endpoints.
"""
from rest_framework import serializers
from voting.models import Election, Candidate, Position


class CandidateSerializer(serializers.ModelSerializer):
    photo_url = serializers.ReadOnlyField()
    vote_count = serializers.ReadOnlyField()

    class Meta:
        model = Candidate
        fields = ['id', 'name', 'bio', 'photo_url', 'vote_count']


class PositionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)

    class Meta:
        model = Position
        fields = ['id', 'title', 'description', 'candidates']


class ElectionSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField()
    total_votes = serializers.ReadOnlyField()
    positions = PositionSerializer(many=True, read_only=True)

    class Meta:
        model = Election
        fields = [
            'id', 'name', 'description', 'start_time', 'end_time',
            'status', 'is_published', 'total_votes', 'positions'
        ]


class ResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ['id', 'name', 'is_published']
