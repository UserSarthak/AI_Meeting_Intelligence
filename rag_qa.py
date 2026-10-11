import redis


from langchain_groq import ChatGroq
from dotenv import load_dotenv

from rag_service import (
    search_similar_meetings,
    search_meeting,
    search_action_items,
    redis_client,
    get_rag_cache_key
)

load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


def answer_question(question: str):

    # Check Redis cache
    cache_key = get_rag_cache_key(question)

    try:
        cached_answer = redis_client.get(cache_key)

        if cached_answer:
            return cached_answer

    except redis.RedisError:
        print("Redis cache unavailable. Continuing without cache.")

    # Retrieve relevant meeting chunks
    try:
        results = search_similar_meetings(
            question,
            k=5
        )

        action_items = search_action_items(question)

    except Exception:
        print("Meeting information retrieval failed.")
        return "Unable to retrieve meeting information right now. Please try again later."

    # If nothing was found
    if not results and not action_items:
        return "I could not find any relevant meeting information."

    # Combine retrieved chunks into context
    context = "\n\n".join(
        result.page_content
        for result in results
    )

    action_context = "\n\n".join(
        f"Task: {item['task']}\n"
        f"Assigned To: {item['assigned_to']}\n"
        f"Deadline: {item['deadline']}"
        for item in action_items
    )

    if action_context:
        context += "\n\nStructured action items:\n" + action_context

    

    # print("\n--- RETRIEVED CONTEXT ---")
    # print(context)
    # print("--- END CONTEXT ---\n")

    # Create prompt
    prompt = f"""
    You are an AI meeting assistant.

    Answer the user's question using only the meeting information provided below.

    The meeting information may contain:
    1. Meeting transcript information.
    2. Structured action-item information.

    For questions about tasks, responsibilities, assigned people, or deadlines,
    use the structured action-item information when it is available.

    Do not invent information that is not supported by the provided context.

    If the answer cannot be determined from the provided information,
    say that the information is not available.

    Meeting information:
    {context}

    User question:
    {question}

    Answer:
    """

    # Ask the LLM
    try:
        response = llm.invoke(prompt)
        answer = response.content

    except Exception:
        print("LLM answer generation failed.")
        return "Unable to generate an answer right now. Please try again later."

    # Store answer in Redis for 10 minutes
    try:
        redis_client.setex(
            cache_key,
            600,
            answer
        )
    except redis.RedisError:
        print("Could not cache the answer in Redis.")

    return answer


def answer_meeting_question(question: str, meeting_id: int):

    # Check Redis cache
    cache_key = get_rag_cache_key(
        question,
        meeting_id
    )

    try:
        cached_answer = redis_client.get(cache_key)

        if cached_answer:
            return cached_answer

    except redis.RedisError:
        print("Redis cache unavailable. Continuing without cache.")

    # Retrieve relevant chunks and action items
    try:
        results = search_meeting(
            question,
            meeting_id,
            k=5
        )

        action_items = search_action_items(question)

    except Exception:
        print("Meeting-specific information retrieval failed.")
        return "Unable to retrieve meeting information right now. Please try again later."


    # Keep only action items belonging to this meeting
    action_items = [
        item
        for item in action_items
        if item["meeting_id"] == meeting_id
    ]

    # If nothing was found
    if not results and not action_items:
        return "I could not find any relevant information in this meeting."

    context = "\n\n".join(
        result.page_content
        for result in results
    )

    action_context = "\n\n".join(
        f"Task: {item['task']}\n"
        f"Assigned To: {item['assigned_to']}\n"
        f"Deadline: {item['deadline']}"
        for item in action_items
    )

    if action_context:
        context += "\n\nStructured action items:\n" + action_context

    prompt = f"""
You are an AI meeting assistant.

Answer the user's question using only the information from Meeting {meeting_id} provided below.

For questions about tasks, responsibilities, assigned people, or deadlines,
use the structured action-item information when it is available.

Do not invent information.

If the answer cannot be determined from this meeting,
say that the information is not available.

Meeting information:
{context}

User question:
{question}

Answer:
"""

    try:
        response = llm.invoke(prompt)
        answer = response.content

    except Exception:
        print("Meeting-specific LLM answer generation failed.")
        return "Unable to generate an answer right now. Please try again later."

    # Store answer in Redis for 10 minutes
    try:
        redis_client.setex(
            cache_key,
            600,
            answer
        )
    except redis.RedisError:
        print("Could not cache the answer in Redis.")

    return answer


