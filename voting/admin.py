"""
voting/admin.py
Admin registration for election management models.
"""
from django.contrib import admin
from .models import Election, Position, Candidate, Vote, UserElectionMapping


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1
    fields = ['name', 'bio', 'photo']


class UserElectionMappingInline(admin.TabularInline):
    model = UserElectionMapping
    fk_name = 'election'
    extra = 1
    fields = ['user', 'assigned_at']
    readonly_fields = ['assigned_at']


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time', 'status', 'is_published', 'total_votes']
    list_filter = ['is_published']
    search_fields = ['name']
    inlines = [PositionInline, UserElectionMappingInline]

    def status(self, obj):
        return obj.status
    status.short_description = 'Status'


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'election', 'order']
    list_filter = ['election']
    inlines = [CandidateInline]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'vote_count']
    list_filter = ['position__election']
    search_fields = ['name']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'candidate', 'election', 'position', 'timestamp']
    list_filter = ['election']
    readonly_fields = ['voter', 'candidate', 'election', 'position', 'timestamp']


@admin.register(UserElectionMapping)
class UserElectionMappingAdmin(admin.ModelAdmin):
    list_display = ['user', 'election', 'assigned_at']
    list_filter = ['election']
    search_fields = ['user__username', 'election__name']
