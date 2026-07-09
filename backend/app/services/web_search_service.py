"""
Safe Web Search Fallback Service - SehatSaathi

Purpose:
Used ONLY when local medical RAG confidence is low.

Flow:

Local Medical KB
        |
 confidence low
        |
        ↓
Controlled Web Search

        ↓

Safety validation

        ↓

Return general guidance


Important:
- Web is NOT primary medical knowledge source
- Never diagnose
- Never prescribe
"""


import os
import logging

from pathlib import Path

from dotenv import load_dotenv

from groq import Groq


# =========================
# CONFIG
# =========================


BASE_DIR = Path(__file__).resolve().parents[3]


load_dotenv(
    BASE_DIR / ".env"
)


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


MODEL_NAME = "groq/compound"


_client = None



logging.basicConfig(
    level=logging.INFO
)



# =========================
# CLIENT
# =========================


def get_client():

    """
    Lazy initialize Groq client
    """

    global _client


    if _client is None:


        if not GROQ_API_KEY:


            raise RuntimeError(
                "Missing GROQ_API_KEY"
            )


        _client = Groq(

            api_key=GROQ_API_KEY

        )


    return _client



# =========================
# BASIC EMERGENCY CHECK
# =========================


WEB_BLOCKED_SYMPTOMS = [

    "chest pain",

    "difficulty breathing",

    "unconscious",

    "severe bleeding",

    "stroke",

    "suicide",

    "seizure"

]



def emergency_precheck(
        query:str
):

    """
    Do not answer dangerous cases
    using web search.
    """


    text=query.lower()


    for symptom in WEB_BLOCKED_SYMPTOMS:


        if symptom in text:


            return True


    return False



# =========================
# RESPONSE SAFETY CHECK
# =========================


def validate_web_response(
        answer:str
):

    """
    Prevent unsafe medical claims
    """

    banned=[

        "you definitely have",

        "you are suffering from",

        "stop taking",

        "ignore your doctor",

        "guaranteed cure",

        "no need to see a doctor"

    ]


    lower=answer.lower()


    for phrase in banned:


        if phrase in lower:


            return False


    return True



# =========================
# MAIN WEB FALLBACK
# =========================



def web_search_fallback(
        query:str
):

    """
    Called when:

    RAG confidence < threshold

    Returns structured response
    """


    try:


        # ------------------
        # emergency blocking
        # ------------------


        if emergency_precheck(query):


            return {


                "answer":

                (
                "Your symptoms may require urgent "
                "medical attention. Please contact "
                "a healthcare professional or visit "
                "the nearest facility."
                ),


                "source":

                "safety_override",


                "confidence":

                "high"

            }



        client=get_client()

        system_prompt = """
You are a medical information retrieval assistant.

Your role:
Provide general health information only.

Rules:

1. NEVER diagnose a condition.

2. NEVER say the patient has a disease.

3. NEVER prescribe medicine or dosage.

4. Prefer information from:
   - WHO
   - CDC
   - Government health agencies
   - Recognized hospitals

5. Avoid:
   - forums
   - personal blogs
   - advertisements

6. Mention uncertainty clearly.

7. Recommend consulting healthcare
   professionals when appropriate.

8. Keep answer simple because users may
   have low medical literacy.

Return:
- possible general explanation
- when to seek care
- no diagnosis

Maximum 5 sentences.

"""

        # Truncate query if too long to prevent 413 errors
        query_for_request = query[:500] if len(query) > 500 else query

        # Build the initial (rich) messages payload so we can inspect size if needed
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
Patient symptom query:

{query_for_request}

Give safe general guidance.
""",
            },
        ]

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.2,
            )

        except Exception as api_error:
            # Robust detection for payload-too-large style errors
            err_text = str(api_error).lower()
            status_code = getattr(api_error, "status_code", None) or getattr(api_error, "status", None)
            is_413 = False
            if status_code == 413:
                is_413 = True
            if "413" in err_text or "payload too large" in err_text or "request entity too large" in err_text:
                is_413 = True

            if is_413:
                logging.error(f"Web search request too large: {api_error}")

                # Print size diagnostics for the original payload
                try:
                    total_len = sum(len(m.get("content", "")) for m in messages)
                    logging.info(f"Original payload length: {total_len}")
                    logging.info(f"Original payload preview: {messages[1].get('content','')[:500]}")
                except Exception:
                    pass

                # Attempt a compact retry with a minimal system prompt and much shorter query
                compact_system = (
                    "You are a medical information assistant. Provide a very brief, non-diagnostic reply. "
                    "Use no more than 2 short sentences. Do NOT diagnose, do NOT prescribe."
                )

                compact_query = query_for_request.strip().split('\n')[0][:300]

                compact_messages = [
                    {"role": "system", "content": compact_system},
                    {"role": "user", "content": compact_query},
                ]

                # Diagnostic print for compact payload size — must be small (≈300–800 chars)
                try:
                    compact_len = sum(len(m.get("content", "")) for m in compact_messages)
                    logging.info(f"Compact payload length: {compact_len}")
                    logging.info(f"Compact payload preview: {compact_messages[1].get('content','')[:500]}")
                except Exception:
                    pass

                try:
                    logging.info("Retrying web fallback with compact payload after 413 error")
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=compact_messages,
                        temperature=0.2,
                    )
                except Exception as retry_err:
                    # If we still hit 413 on the compact payload, log and return fallback
                    if "413" in str(retry_err).lower() or "payload too large" in str(retry_err).lower():
                        logging.error(f"Compact retry still too large: {retry_err}")
                        logging.error(f"Compact payload length reported: {compact_len if 'compact_len' in locals() else 'unknown'}")
                    else:
                        logging.error(f"Compact retry failed: {retry_err}")
                    return {
                        "answer": (
                            "I could not retrieve additional information right now. "
                            "Please consult a healthcare professional if symptoms continue or worsen."
                        ),
                        "source": "fallback_error",
                        "confidence": "unknown",
                    }
            else:
                # Re-raise other errors so they surface for debugging
                raise



        answer=(

            response

            .choices[0]

            .message

            .content

        )



        # ------------------
        # validate output
        # ------------------


        if not validate_web_response(answer):


            logging.warning(

                "Unsafe web response blocked"

            )


            return {


                "answer":

                (
                "I could not provide reliable "
                "information for this symptom. "
                "Please consult a healthcare worker."
                ),


                "source":

                "blocked_web_response",


                "confidence":

                "low"

            }



        return {


            "answer":answer,


            "source":

            "web_fallback",



            "confidence":

            "low",



            "disclaimer":

            (
            "This information comes from web search "
            "because local verified guidelines did "
            "not contain enough information."
            )

        }




    except Exception as e:


        logging.error(

            f"Web fallback failed: {e}"

        )



        return {


            "answer":

            (
            "I could not retrieve additional "
            "information right now. Please contact "
            "a healthcare professional if symptoms "
            "continue or worsen."
            ),


            "source":

            "fallback_error",


            "confidence":

            "unknown"

        }