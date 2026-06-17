"""
Query rewriting service

Converts user conversation into a better
medical retrieval query.

Example:
"My head hurts since yesterday"

↓

"Patient reports headache duration one day symptoms"
"""


def rewrite_query(
        llm_call,
        query:str
):


    messages=[

        {
            "role":"system",

            "content":
            """
You rewrite user health queries for medical document retrieval.

Rules:
- Keep symptoms
- Keep duration
- Keep severity
- Remove unnecessary conversation words
- Do NOT diagnose

Return only rewritten query text.
"""
        },


        {
            "role":"user",

            "content":query
        }

    ]



    response = llm_call(
        messages
    )



    return response.strip()