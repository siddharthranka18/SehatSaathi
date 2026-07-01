import os
import json
import re
import time
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
You are SehatSaathi, an AI medical triage assistant.

Your job is to estimate the urgency of the user's condition.
You are NOT a doctor.
Never diagnose diseases or claim medical certainty.

Your responsibilities:

1. Understand the symptoms.
2. Estimate urgency using ONLY the supplied medical context.
3. Ask follow-up questions ONLY when absolutely necessary.
4. Produce a final triage decision as soon as sufficient information is available.

Urgency Levels:

home_care
- Mild symptoms.
- Self-care is usually appropriate.

visit_phc
- Needs evaluation by a healthcare professional within 24-48 hours.
- If uncertain between home_care and visit_phc, choose visit_phc.

critical
- Possible medical emergency.
- Immediate medical attention is required.

Decision Rules:

• Never invent medical information.
• Never ignore the supplied medical context.
• Never diagnose diseases.
• Never recommend prescription medicines.
• Always reply in the user's language.
• Always include:
"This is guidance, not a medical diagnosis."

Follow-up Question Rules:

Ask follow-up questions ONLY if the urgency cannot reasonably be determined.

DO NOT ask follow-up questions if:
- enough information already exists,
- the urgency is already obvious,
- emergency symptoms are present.

Examples of obvious emergency situations:
- chest pain with breathing difficulty
- unconsciousness
- stroke symptoms
- severe bleeding
- snake bite
- poisoning
- electric shock
- severe burns
- seizures

For these cases:
- urgency = "critical"
- is_final = true

Likewise, if the available symptoms are already sufficient to classify as
home_care or visit_phc,
return the FINAL decision immediately.

Never ask unnecessary questions simply to gather more information.

Maximum follow-up questions:
4

Return ONLY valid JSON.

{
  "reply":"...",
  "urgency":"home_care|visit_phc|critical|unclear",
  "is_final":true
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

    pipeline_timings = {}
    total_start = time.perf_counter()

    full_text = " ".join([m.content for m in request.conversation])

    # 1. SAFETY CHECK
    t0 = time.perf_counter()
    safety = check_red_flags(full_text)
    pipeline_timings["safety_check"] = round(time.perf_counter() - t0, 4)

    if safety["urgent"]:
        pipeline_timings["total"] = round(time.perf_counter() - total_start, 4)
        return TriageResponse(
            reply=safety["message"],
            urgency="critical",
            is_final=True,
            source="safety_override",
            pipeline_timings=pipeline_timings,
        )

    # 2. QUERY REWRITE
    t0 = time.perf_counter()
    rewritten_query = rewrite_query(chat_completion, full_text)
    pipeline_timings["rewrite"] = round(time.perf_counter() - t0, 4)
    print("REWRITTEN QUERY:", rewritten_query)

    # 3. RAG RETRIEVAL
    t0 = time.perf_counter()
    rag_result = retrieve_context(rewritten_query)
    pipeline_timings["rag"] = round(time.perf_counter() - t0, 4)

    print("\n========== TRIAGE DEBUG ==========")
    print("RAG Source:", "medical_guideline_rag" if rag_result["confident"] else "web_fallback")
    print("Top Score:", rag_result["top_score"])
    print("==================================\n")

    # 4. CONTEXT SELECTION
    t0 = time.perf_counter()
    if rag_result["confident"]:
        context = "\n\n".join(rag_result["chunks"])
        source = "medical_guideline_rag"
        pipeline_timings["web_fallback"] = 0.0
    else:
        web_result = web_search_fallback(rewritten_query)
        context = f"""
UNVERIFIED WEB INFORMATION

{web_result["answer"]}

Use this only if it does not contradict the provided medical reasoning.
Clearly mention that this information is from web search and may not be clinically verified.
"""
        source = "web_fallback"
        pipeline_timings["web_fallback"] = round(time.perf_counter() - t0, 4)

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

    # 7. LLM GENERATION
    t0 = time.perf_counter()
    raw = chat_completion_json(messages)
    pipeline_timings["llm"] = round(time.perf_counter() - t0, 4)
    print("RAW LLM:", raw)

    # 8. JSON PARSE
    t0 = time.perf_counter()
    try:
        parsed = parse_llm_json(raw)
        pipeline_timings["json_parse"] = round(time.perf_counter() - t0, 4)
    except Exception as e:
        pipeline_timings["json_parse"] = round(time.perf_counter() - t0, 4)
        pipeline_timings["total"] = round(time.perf_counter() - total_start, 4)
        print("JSON ERROR:", e)
        return TriageResponse(
            reply="I could not understand properly. Please explain again.",
            urgency="unclear",
            is_final=False,
            source="json_parse_error",
            pipeline_timings=pipeline_timings,
        )

    # 9. OUTPUT SAFETY
    t0 = time.perf_counter()
    safe = validate_ai_response(parsed.get("reply", ""))
    pipeline_timings["output_safety"] = round(time.perf_counter() - t0, 4)

    pipeline_timings["total"] = round(time.perf_counter() - total_start, 4)

    if not safe["safe"]:
        return TriageResponse(
            reply="Please consult a healthcare professional for proper guidance.",
            urgency="visit_phc",
            is_final=True,
            source="output_guardrail",
            pipeline_timings=pipeline_timings,
        )

    # FINAL RESPONSE
    return TriageResponse(
        reply=parsed.get("reply", ""),
        urgency=parsed.get("urgency", "unclear"),
        is_final=parsed.get("is_final", False),
        source=source,
        confidence=rag_result["top_score"],
        retrieved_sources=rag_result.get("retrieved_sources", []),
        pipeline_timings=pipeline_timings,
        rag_timings=rag_result.get("timings", {}),
        dense_hits=rag_result.get("dense_hits", 0),
        bm25_hits=rag_result.get("bm25_hits", 0),
        retrieved_chunks=rag_result.get("retrieved_chunks", 0),
    )