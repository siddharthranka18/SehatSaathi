import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from ..models.schemas import TriageRequest, TriageResponse
from .rag_service import retrieve_context
from .query_service import rewrite_query
from .safety_service import check_red_flags, validate_ai_response
from .web_search_service import web_search_fallback

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def chat_completion(messages: list[dict]):
    """Plain text completion — used for query rewriting."""
    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content


def chat_completion_json(messages: list[dict]):
    """JSON mode completion — used for triage responses."""
    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content


SYSTEM_PROMPT = """
You are SehatSaathi, a safe medical triage assistant.
You are NOT a doctor.
Never diagnose disease names.

Your tasks:
1. Understand symptoms.
2. Ask only necessary follow-up questions.
3. Classify urgency.

Categories:
home_care: Mild symptoms.
visit_phc: Needs healthcare visit within 24-48 hours.
critical: Needs urgent medical attention.

Rules:
- Use provided medical context.
- Never invent medical facts.
- If uncertain choose visit_phc.
- Maximum 3-4 follow-up questions.
- Reply in user's language.
- Mention: "This is guidance, not diagnosis."

Return ONLY valid JSON:
{
"reply":"message",
"urgency":"home_care|visit_phc|critical|unclear",
"is_final":true/false
}
"""


def parse_llm_json(raw):
    raw = raw.strip()
    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group()
    return json.loads(raw)


def run_triage(request: TriageRequest) -> TriageResponse:

    full_text = " ".join([m.content for m in request.conversation])

    # 1. SAFETY CHECK
    safety = check_red_flags(full_text)
    if safety["urgent"]:
        return TriageResponse(
            reply=safety["message"],
            urgency="critical",
            is_final=True,
            source="safety_override"
        )

    # 2. QUERY REWRITE — plain text mode, no json enforcement
    rewritten_query = rewrite_query(chat_completion, full_text)
    print("REWRITTEN QUERY:", rewritten_query)

    # 3. RAG RETRIEVAL
    rag_result = retrieve_context(rewritten_query)
    print("\n========== TRIAGE DEBUG ==========")
    print("RAG Source:", "medical_guideline_rag" if rag_result["confident"] else "web_fallback")
    print("Top Score:", rag_result["top_score"])
    print("==================================\n")

    # 4. CONTEXT SELECTION
    if rag_result["confident"]:
        context = "\n\n".join(rag_result["chunks"])
        source = "medical_guideline_rag"
    else:
        web_result = web_search_fallback(rewritten_query)
        context = f"""
UNVERIFIED WEB INFORMATION

{web_result["answer"]}

Use this only if it does not contradict the provided medical reasoning.
Clearly mention that this information is from web search and may not be clinically verified.
"""
        source = "web_fallback"

    # 5. BUILD LLM MESSAGES
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + f"\n\nVerified Medical Context:\n\n{context}"
        }
    ]

    for m in request.conversation:
        messages.append({"role": m.role, "content": m.content})

    # 6. FOLLOW-UP LIMIT
    assistant_turns = sum(1 for m in request.conversation if m.role == "assistant")
    if assistant_turns >= 4:
        messages.append({
            "role": "system",
            "content": "You have asked enough questions. Return your FINAL triage decision now. Set is_final=true."
        })

    # 7. LLM GENERATION — json mode
    raw = chat_completion_json(messages)
    print("RAW LLM:", raw)

    # 8. JSON PARSE
    try:
        parsed = parse_llm_json(raw)
    except Exception as e:
        print("JSON ERROR:", e)
        return TriageResponse(
            reply="I could not understand properly. Please explain again.",
            urgency="unclear",
            is_final=False,
            source="json_parse_error"
        )

    # 9. OUTPUT SAFETY
    safe = validate_ai_response(parsed.get("reply", ""))
    if not safe["safe"]:
        return TriageResponse(
            reply="Please consult a healthcare professional for proper guidance.",
            urgency="visit_phc",
            is_final=True,
            source="output_guardrail"
        )

    # FINAL RESPONSE
    return TriageResponse(
        reply=parsed.get("reply", ""),
        urgency=parsed.get("urgency", "unclear"),
        is_final=parsed.get("is_final", False),
        source=source
    )