import os
import json

from pathlib import Path
from dotenv import load_dotenv

from groq import Groq


from app.models.schemas import (
    TriageRequest,
    TriageResponse
)


from app.services.rag_service import (
    retrieve_context
)


from app.services.query_service import (
    rewrite_query
)


from app.services.safety_service import (
    check_red_flags,
    validate_ai_response
)


from app.services.web_search_service import (
    web_search_fallback
)



# ==========================
# ENV + GROQ
# ==========================


BASE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(
    BASE_DIR / ".env"
)


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    ""
)


GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.1-70b-versatile"
)


_client=None



def get_client():

    global _client


    if _client is None:


        _client=Groq(
            api_key=GROQ_API_KEY
        )


    return _client



# ==========================
# LLM CALL
# ==========================


def chat_completion(
        messages:list[dict]
):


    client=get_client()


    response=client.chat.completions.create(

        model=GROQ_MODEL,

        messages=messages,

        temperature=0.2

    )


    return response.choices[0].message.content





# ==========================
# SYSTEM PROMPT
# ==========================


SYSTEM_PROMPT = """

You are SehatSaathi,
a careful health triage assistant for India.


IMPORTANT:

You are NOT a doctor.

Never diagnose diseases.

Your job is only:

- understand symptoms
- ask needed follow-up questions
- provide urgency guidance


Possible urgency:


home_care:
Mild symptoms


visit_phc:
Should visit healthcare worker
within 24-48 hours


critical:
Needs urgent medical attention


Rules:

1.
Use the provided medical context.

2.
Do not invent medical facts.

3.
If uncertain choose visit_phc.

4.
Ask maximum 3-4 follow-up questions.

5.
If enough information exists,
give final answer.

6.
Speak in user's language.

7.
Always mention:
"This is guidance, not diagnosis."


Return ONLY JSON:


{
"reply":"message",
"urgency":"home_care|visit_phc|critical|unclear",
"is_final":true/false
}

"""




# ==========================
# MAIN TRIAGE PIPELINE
# ==========================



def run_triage(
        request:TriageRequest
)->TriageResponse:



    # combine conversation


    full_text=" ".join(

        [
            m.content

            for m in request.conversation
        ]

    )



    # ======================
    # 1. HARD SAFETY CHECK
    # ======================


    safety=check_red_flags(
        full_text
    )


    if safety["urgent"]:


        return TriageResponse(

            reply=safety["message"],

            urgency="critical",

            is_final=True,

            source="safety_override"

        )




    # ======================
    # 2. QUERY REWRITE
    # ======================



    rewritten_query = rewrite_query(

        chat_completion,

        full_text

    )





    # ======================
    # 3. ADVANCED RAG
    # ======================



    rag_result=retrieve_context(

        rewritten_query

    )





    # ======================
    # 4. CONTEXT SELECTION
    # ======================



    if rag_result["confident"]:


        context="\n\n".join(

            rag_result["chunks"]

        )


        source="medical_guideline_rag"



    else:


        web_result=web_search_fallback(

            rewritten_query

        )


        context=web_result["answer"]


        source="web_fallback"





    # ======================
    # 5. FOLLOW-UP LIMIT
    # ======================



    assistant_turns=sum(

        1

        for m in request.conversation

        if m.role=="assistant"

    )




    messages=[


        {
            "role":"system",

            "content":

            SYSTEM_PROMPT

            +

            f"""



Verified Medical Context:


{context}

"""

        }

    ]





    for m in request.conversation:


        messages.append({

            "role":m.role,

            "content":m.content

        })





    if assistant_turns>=4:



        messages.append({


            "role":"system",


            "content":

            """

You have enough information.

Do not ask more questions.

Return final urgency classification.

"""

        })





    # ======================
    # 6. GENERATE ANSWER
    # ======================



    raw=chat_completion(

        messages

    )




    # ======================
    # 7. PARSE JSON
    # ======================



    try:


        parsed=json.loads(
            raw
        )



    except json.JSONDecodeError:



        return TriageResponse(


            reply=

            "Could you describe your symptoms again?",


            urgency="unclear",


            is_final=False,


            source="json_parse_error"

        )





    # ======================
    # 8. OUTPUT SAFETY CHECK
    # ======================



    safe=validate_ai_response(

        parsed.get(
            "reply",
            ""
        )

    )



    if not safe["safe"]:


        return TriageResponse(

            reply=

            "Please consult a healthcare professional for proper guidance.",


            urgency="visit_phc",


            is_final=True,


            source="output_guardrail"

        )





    # ======================
    # FINAL RESPONSE
    # ======================



    return TriageResponse(


        reply=parsed.get(
            "reply",
            ""
        ),


        urgency=parsed.get(

            "urgency",

            "unclear"

        ),


        is_final=parsed.get(

            "is_final",

            False

        ),


        source=source

    )