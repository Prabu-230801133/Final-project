"""
chat/context.py
Builds a rich, structured context string from the live database
that gets injected into every Gemini request as system knowledge.
"""
from django.utils import timezone
from voting.models import Election, Candidate, Vote, Position
from accounts.models import CustomUser


def build_election_context():
    """
    Query live DB and return a structured string describing:
    - All elections (active, scheduled, ended/published)
    - Positions and candidates per election
    - Vote counts & statistics (only for published elections)
    - Overall platform stats
    """
    now = timezone.now()
    lines = []

    # ── Platform overview ─────────────────────────────────────────────────────
    total_users   = CustomUser.objects.filter(role='student').count()
    total_votes   = Vote.objects.count()
    total_elections = Election.objects.count()

    lines.append("=== VoteX College Voting Platform ===")
    lines.append(f"Total registered students: {total_users}")
    lines.append(f"Total votes cast (all time): {total_votes}")
    lines.append(f"Total elections ever held: {total_elections}")
    lines.append("")

    # ── Active elections ──────────────────────────────────────────────────────
    active = Election.objects.filter(start_time__lte=now, end_time__gte=now)
    if active.exists():
        lines.append("=== ACTIVE ELECTIONS (voting open now) ===")
        for e in active:
            lines.append(f"• Election: {e.name}")
            lines.append(f"  Description: {e.description or 'N/A'}")
            lines.append(f"  Voting closes: {e.end_time.strftime('%d %b %Y, %I:%M %p')}")
            lines.append(f"  Votes cast so far: {e.total_votes}")
            lines.append(f"  Eligible voters: {e.eligible_voters_count}")
            for pos in e.positions.prefetch_related('candidates').all():
                cands = ', '.join(c.name for c in pos.candidates.all())
                lines.append(f"  Position '{pos.title}' — Candidates: {cands or 'None yet'}")
            lines.append("")
    else:
        lines.append("=== No elections are currently active. ===\n")

    # ── Scheduled elections ───────────────────────────────────────────────────
    scheduled = Election.objects.filter(start_time__gt=now)
    if scheduled.exists():
        lines.append("=== UPCOMING / SCHEDULED ELECTIONS ===")
        for e in scheduled:
            lines.append(f"• Election: {e.name}")
            lines.append(f"  Starts: {e.start_time.strftime('%d %b %Y, %I:%M %p')}")
            lines.append(f"  Ends:   {e.end_time.strftime('%d %b %Y, %I:%M %p')}")
            for pos in e.positions.prefetch_related('candidates').all():
                cands = ', '.join(c.name for c in pos.candidates.all())
                lines.append(f"  Position '{pos.title}' — Candidates: {cands or 'TBA'}")
            lines.append("")

    # ── Published results ─────────────────────────────────────────────────────
    published = Election.objects.filter(is_published=True, end_time__lt=now)
    if published.exists():
        lines.append("=== PUBLISHED ELECTION RESULTS ===")
        for e in published:
            lines.append(f"• Election: {e.name}  (Total votes: {e.total_votes})")
            for pos in e.positions.prefetch_related('candidates').all():
                total = sum(c.vote_count for c in pos.candidates.all())
                lines.append(f"  Position: {pos.title}  (Total: {total} votes)")
                candidates = sorted(
                    pos.candidates.all(),
                    key=lambda c: c.vote_count,
                    reverse=True
                )
                for rank, c in enumerate(candidates, 1):
                    pct = round(c.vote_count / total * 100, 1) if total else 0
                    tag = " ← WINNER" if rank == 1 and total > 0 else ""
                    lines.append(f"    {rank}. {c.name}: {c.vote_count} votes ({pct}%){tag}")
            lines.append("")

    # ── Site navigation guide ─────────────────────────────────────────────────
    lines.append("=== SITE NAVIGATION GUIDE ===")
    lines.append("• Home page (/)                    — Public landing page with election highlights & results")
    lines.append("• Login (/accounts/login/)          — Log in with username/password OR Google account")
    lines.append("• Student Dashboard (/voting/dashboard/) — View your assigned elections and cast votes")
    lines.append("• Admin Dashboard (/admin-dashboard/)   — Web admin: manage elections, candidates, students")
    lines.append("• API (/api/elections/)              — Public REST API for elections data")
    lines.append("• Results are shown on the home page once an admin publishes them")
    lines.append("")
    lines.append("=== HOW VOTING WORKS ===")
    lines.append("1. An admin creates an election and assigns students to it.")
    lines.append("2. Students log in and see their assigned elections on the dashboard.")
    lines.append("3. Students vote for one candidate per position.")
    lines.append("4. You can only vote ONCE per position per election.")
    lines.append("5. Results are hidden until the admin publishes them.")
    lines.append("6. Voting closes at the election end time.")

    return "\n".join(lines)
