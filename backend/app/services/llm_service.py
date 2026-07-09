import os
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from ..models.schemas import TriageRequest, TriageResponse, RetrievalStats
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
- Mild or self-limiting symptoms (e.g., minor ache, mild nausea, localized discomfort).
- Symptoms have improved or remained stable.
- No emergency red flags.
- Self-care, rest, hydration, and monitoring are appropriate.

visit_phc
- Moderate symptoms or concerning patterns (e.g., persistent fever >38°C with additional symptoms, worsening pain, functional impact).
- Symptoms lasting longer than a few days without improvement.
- Need for professional evaluation within 24–48 hours to rule out complications.
- Clear guideline thresholds met for medical attention.

critical
- Possible medical emergency requiring immediate attention.
- Severe symptoms (e.g., chest pain, difficulty breathing, altered consciousness, severe bleeding).
- Symptoms meeting explicit emergency criteria in the guidelines.

Decision Rules:

• Never invent medical information.
• Never ignore the supplied medical context.
• Never diagnose diseases.
• Never recommend prescription medicines.
• Always reply in the user's language.
• Always include:
"This is guidance, not a medical diagnosis."

• When symptoms are mild and localized (single area, low intensity, short duration), recommend home_care with monitoring.
• Only escalate to visit_phc when:
  - Symptom severity is clearly moderate or worsening,
  - Multiple concerning symptoms appear together,
  - Guideline thresholds are explicitly met (e.g., fever >38°C AND duration >2 days),
  - Risk of complications is significant.

When the provided medical context contains explicit thresholds (for example temperature, symptom duration, age, or severity), apply those thresholds exactly. Do not relax, generalize, or infer missing parts to justify a higher urgency. If a guideline requires multiple conditions, ensure all are satisfied before assigning the corresponding urgency. If the user's reported values do not meet every required threshold, prefer recommending lower-intensity care with monitoring or ask one targeted follow-up question to clarify the missing detail; do not escalate urgency without full rule satisfaction.

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

def _normalize_retrieval_stats(stats, query: str = "") -> RetrievalStats:
    if isinstance(stats, RetrievalStats):
        return stats

    if not isinstance(stats, dict):
        stats = {}

    payload = {
        "query": query or stats.get("query", ""),
        "candidate_chunks": stats.get("candidate_chunks", 0),
        "parent_documents": stats.get("parent_documents", 0),
        "reranked_documents": stats.get("reranked_documents", 0),
        "returned_documents": stats.get("returned_documents", 0),
    }

    return RetrievalStats.model_validate(payload)


def run_triage(request: TriageRequest) -> TriageResponse:

    pipeline_timings = {}
    total_start = time.perf_counter()

    full_text = " ".join([m.content for m in request.conversation])
    retrieval_stats = RetrievalStats()

    # Safety check runs only on USER messages — not assistant replies.
    # Running on full_text (including AI responses) causes false positives:
    # e.g. a previous AI reply mentioning "breathing difficulty" would flag
    # the next completely unrelated user message as a breathing emergency.
    user_text = " ".join([m.content for m in request.conversation if m.role == "user"])

    # 1. SAFETY CHECK
    t0 = time.perf_counter()
    safety = check_red_flags(user_text)
    pipeline_timings["safety_check"] = round(time.perf_counter() - t0, 4)

    if safety["urgent"]:
        pipeline_timings["total"] = round(time.perf_counter() - total_start, 4)
        return TriageResponse(
            reply=safety["message"],
            urgency="critical",
            is_final=True,
            source="safety_override",
            pipeline_timings=pipeline_timings,
            rewritten_query="",
            rag_confident=False,
            retrieval_method="Safety Override",
            context_length=0,
            parent_hits=0,
            dense_scores=[],
            reranker_scores=[],
            retrieval_stats=retrieval_stats,
            conversation_turns=len(request.conversation),
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
    retrieval_stats = _normalize_retrieval_stats(
        rag_result.get("retrieval_stats", {}),
        query=rewritten_query,
    )

    print("\n========== TRIAGE DEBUG ==========")
    print("RAG Source:", "medical_guideline_rag" if rag_result["confident"] else "web_fallback")
    print("Top Score:", rag_result["top_score"])
    print("Source keyword match:", rag_result.get("source_keyword_match", "n/a"))
    print("Confident:", rag_result["confident"])
    print("==================================\n")

    # 4. CONTEXT SELECTION
    t0 = time.perf_counter()
    # rag_result["confident"] is the single source of truth.
    # It is computed inside retrieve_context() using get_confidence_threshold()
    # (which reads threshold.json if present) AND a source-keyword match override
    # (if the top retrieved file's name contains a query keyword, trust it even
    # when the numeric score is low).
    # We do NOT re-evaluate the threshold here to avoid having two thresholds.
    rag_confident_flag = rag_result.get("confident", False)

    if rag_confident_flag:
        context = "\n\n".join(rag_result["chunks"])
        source = "medical_guideline_rag"
        # Respect the retrieval_method set by rag_service (e.g. "BM25 Only (FAST_DEV=1)")
        # so evaluation reports and API responses are always honest about the pipeline used.
        retrieval_method = rag_result.get("retrieval_method", "Hybrid RAG")
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
        retrieval_method = "Web Fallback"

        pipeline_timings["web_fallback"] = round(
            time.perf_counter() - t0,
            4
        )

    context_length = len(context)
    conversation_turns = len(request.conversation)

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
            rewritten_query=rewritten_query,
            rag_confident=rag_result.get("confident", False),
            retrieval_method=retrieval_method,
            context_length=context_length,
            parent_hits=rag_result.get("parent_hits", 0),
            dense_scores=rag_result.get("dense_scores", []),
            reranker_scores=rag_result.get("reranker_scores", []),
            retrieval_stats=retrieval_stats,
            conversation_turns=conversation_turns,
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
            rewritten_query=rewritten_query,
            rag_confident=rag_result.get("confident", False),
            retrieval_method=retrieval_method,
            context_length=context_length,
            parent_hits=rag_result.get("parent_hits", 0),
            dense_scores=rag_result.get("dense_scores", []),
            reranker_scores=rag_result.get("reranker_scores", []),
            retrieval_stats=retrieval_stats,
            conversation_turns=conversation_turns,
        )

    # FINAL RESPONSE
    return TriageResponse(
        reply=parsed.get("reply", ""),
        urgency=parsed.get("urgency", "unclear"),
        is_final=parsed.get("is_final", False),
        source=source,
        confidence=rag_result.get("top_score", 0),
        retrieved_sources=rag_result.get("retrieved_sources", []),
        pipeline_timings=pipeline_timings,
        rag_timings=rag_result.get("timings", {}),
        dense_hits=rag_result.get("dense_hits", 0),
        bm25_hits=rag_result.get("bm25_hits", 0),
        parent_hits=rag_result.get("parent_hits", 0),
        retrieved_chunks=rag_result.get("retrieved_chunks", 0),
        rewritten_query=rewritten_query,
        rag_confident=rag_result.get("confident", False),
        retrieval_method=retrieval_method,
        context_length=context_length,
        dense_scores=rag_result.get("dense_scores", []),
        reranker_scores=rag_result.get("reranker_scores", []),
        retrieval_stats=retrieval_stats,
        conversation_turns=conversation_turns,
    )