"""
Query transformation service

Responsible for:
- conversational query rewriting
- voice/noisy input normalization
- better retrieval queries

Runs BEFORE RAG retrieval
"""


from langchain_core.prompts import ChatPromptTemplate


def rewrite_query(
        llm,
        user_query:str,
        chat_history:str=""
):

    prompt = ChatPromptTemplate.from_template(
        """
You are a medical search query optimizer.

Your job:
Rewrite the patient's message into a clear
medical retrieval query.

Rules:
- Do NOT diagnose
- Do NOT add symptoms
- Keep all symptoms mentioned
- Expand unclear words
- Preserve urgency indicators
- Include time duration if mentioned


Conversation history:
{history}


Patient message:
{query}


Optimized search query:
"""
    )


    chain = prompt | llm


    response = chain.invoke({

        "query":user_query,

        "history":chat_history

    })


    return response.content