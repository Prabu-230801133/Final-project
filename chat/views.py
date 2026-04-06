"""
chat/views.py
Chatbot endpoint powered by Groq (groq.com) — ultra-fast LLM inference.
Uses Llama 3 via the official Groq Python SDK.
"""
import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .context import build_election_context

logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are VoteX Assistant, a friendly and knowledgeable AI chatbot embedded in the VoteX College Voting Platform.

Your responsibilities:
1. Answer questions about ongoing, upcoming, or past elections using the real-time data provided below.
2. Help students navigate the site (login, dashboard, voting process, etc.).
3. Answer statistics questions about votes, candidates, turnout, and results — but ONLY share results that are marked as published.
4. Be concise, friendly, and helpful. Use emojis sparingly (🗳️, ✅, 📊) to keep it friendly.
5. If you don't know something or it's outside your scope, say so politely.
6. NEVER make up candidate names, vote counts, or results. Only use the data provided below.
7. If the user asks about who won or results, check if the election is published; if not, say results aren't released yet.
8. Keep answers short unless the user asks for details — aim for 2–4 sentences by default.

LIVE PLATFORM DATA (updated in real-time):
---
{context}
---

If a student asks "how do I vote?", walk them through the steps.
If they ask about a specific candidate or election not in the data, say it might not exist or isn't published yet.
"""


def get_groq_response(user_message: str, chat_history: list, db_context: str) -> str:
    """
    Call Groq API with Llama 3.3 70B and return the assistant reply.
    Gracefully falls back if the API key is missing or the call fails.
    """
    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        return (
            "🤖 I'm VoteX Assistant! The AI backend isn't configured yet — "
            "please ask the admin to add a GROQ_API_KEY to the .env file. "
            "You can get a free key at https://console.groq.com/keys\n\n"
            "In the meantime: visit /voting/dashboard/ to vote, "
            "or /accounts/login/ to log in!"
        )

    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        # Build message list: system → history (last 10 turns) → current message
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(context=db_context),
            }
        ]

        for msg in chat_history[-10:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            content = (msg.get("content") or "").strip()
            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Fast, capable, generous free tier
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as exc:
        logger.error("Groq API error: %s", exc)
        return (
            "⚠️ I'm having trouble connecting right now. "
            "Please try again in a moment, or navigate to your dashboard directly."
        )


@csrf_exempt
@require_POST
def chatbot_api(request):
    """
    POST /chat/api/
    Body JSON : { "message": "...", "history": [...] }
    Returns   : { "reply": "..." }
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_message = (data.get('message') or '').strip()
    chat_history = data.get('history', [])

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    if len(user_message) > 1000:
        return JsonResponse({'error': 'Message too long (max 1000 chars)'}, status=400)

    db_context = build_election_context()
    reply = get_groq_response(user_message, chat_history, db_context)

    return JsonResponse({'reply': reply})
