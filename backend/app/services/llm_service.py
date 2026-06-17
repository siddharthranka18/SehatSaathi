import os
import json
from dotenv import load_dotenv
from pathlib import Path
from groq import Groq
from app.models.schemas import TriageRequest, TriageResponse

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
_client = None
def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client
SYSTEM_PROMPT = """You are SehatSaathi, a calm, careful voice-based health triage assistant for India.
You are NOT a doctor and must NEVER give a diagnosis. Your only job is to:

1. Ask up to 3-4 short, simple follow-up questions to understand the symptom, the way a triage nurse would.
2. Once you have enough information, classify the situation into exactly one of:
   - "home_care": mild, manageable at home with general guidance
   - "visit_phc": should see a doctor within 24-48 hours
   - "critical": needs urgent medical attention right now
3. If anything is unclear or even slightly concerning, default to "visit_phc" rather than "home_care" - safety first.
4. Always speak simply and warmly, in the same language the user used.
5. Always remind the user this is general guidance, not a medical diagnosis, when giving a final answer.
6. Do NOT ask follow-up questions just to be thorough. If the user's message already gives you enough information to confidently classify urgency (symptom, duration, and severity are clear), skip straight to a conclusion with is_final: true on the very first turn. Only ask a follow-up question when something critical is genuinely missing or ambiguous.
Respond ONLY in this exact JSON format, with no extra text before or after it:
{"reply": "<message to user>", "urgency": "<home_care|visit_phc|critical|unclear>", "is_final": <true|false>}

Keep "is_final": false and "urgency": "unclear" while you are still asking follow-up questions.
"""

##safetyy check keywords 
RED_FLAGS = [
    {"keywords": ["chest pain", "seene mein dard"], "reason": "Possible cardiac emergency"},
    {"keywords": ["difficulty breathing", "saans lene mein", "shortness of breath"], "reason": "Respiratory distress"},
    {"keywords": ["unconscious", "behosh", "not responding"], "reason": "Loss of consciousness"},
    {"keywords": ["severe bleeding", "bahut khoon"], "reason": "Severe bleeding"},
    {"keywords": ["suicidal", "khud ko nuksan", "self harm"], "reason": "Mental health emergency"},
    {"keywords": ["stroke", "face drooping", "slurred speech"], "reason": "Possible stroke"},
]


def check_red_flags(text: str):
    text = text.lower()
    for flag in RED_FLAGS:
        for kw in flag["keywords"]:
            if kw in text:
                return {"urgency": "critical", "reason": flag["reason"]}
    return None


def chat_completion(messages: list[dict]) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content


def run_triage(request: TriageRequest) -> TriageResponse:
    full_text = " ".join([m.content for m in request.conversation])

    red_flag = check_red_flags(full_text)
    if red_flag:
        return TriageResponse(
            reply="This sounds serious. Please seek urgent medical help immediately or call an ambulance.",
            urgency="critical",
            is_final=True,
            source="hard_rule_override",
        )

    assistant_turns = sum(1 for m in request.conversation if m.role == "assistant")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in request.conversation:
        messages.append({"role": m.role, "content": m.content})

    # Hard cap: after 3 follow-up questions, force a conclusion instead of trusting the model to stop on its own.
    if assistant_turns >= 4:
        messages.append({
            "role": "system",
            "content": (
                "You have already asked enough follow-up questions. Based on everything described so far, "
                "you MUST now conclude with is_final: true and a clear urgency classification "
                "(home_care, visit_phc, or critical). Do not ask any more questions, even if some details are missing."
            ),
        })

    raw = chat_completion(messages)
    ...  # rest stays the same
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return TriageResponse(
            reply="Sorry, could you describe your symptom again in a bit more detail?",
            urgency="unclear",
            is_final=False,
            source="llm_parse_fallback",
        )

    return TriageResponse(
        reply=parsed.get("reply", ""),
        urgency=parsed.get("urgency", "unclear"),
        is_final=parsed.get("is_final", False),
        source="llm",
    )