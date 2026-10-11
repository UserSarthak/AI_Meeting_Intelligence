from langchain_text_splitters import RecursiveCharacterTextSplitter

from vector_store import vector_store
from crud import get_all_meetings, get_action_items

import redis
import json
import hashlib

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

RAG_CACHE_TTL = 600

def get_rag_cache_key(question: str, meeting_id: int | None = None):

    normalized_question = question.strip().lower()

    question_hash = hashlib.md5(
        normalized_question.encode()
    ).hexdigest()

    if meeting_id:
        return f"rag:{meeting_id}:{question_hash}"

    return f"rag:global:{question_hash}"


def clear_rag_cache(meeting_id: int):

    keys = redis_client.keys(f"rag:{meeting_id}:*")

    if keys:
        redis_client.delete(*keys)


def clear_global_rag_cache():

    keys = redis_client.keys("rag:global:*")

    if keys:
        redis_client.delete(*keys)


# Text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)


def add_meeting_to_vector_db(meeting_id: int, transcript: str):

    # Remove existing chunks for this meeting
    existing = vector_store.get(
        where={"meeting_id": meeting_id}
    )

    existing_ids = existing.get("ids", [])

    if existing_ids:
        vector_store.delete(
            ids=existing_ids
        )

    # Split transcript into chunks
    chunks = text_splitter.split_text(transcript)

    # Create metadata for each chunk
    metadatas = [
        {
            "meeting_id": meeting_id
        }
        for _ in chunks
    ]

    # Create unique IDs for each chunk
    ids = [
        f"meeting_{meeting_id}_chunk_{i}"
        for i in range(len(chunks))
    ]

    # Store new chunks
    vector_store.add_texts(
        texts=chunks,
        metadatas=metadatas,
        ids=ids
    )

    print(
        f"Meeting {meeting_id} added to ChromaDB "
        f"in {len(chunks)} chunk(s)"
    )


def index_all_meetings():

    meetings = get_all_meetings()

    indexed_count = 0

    for meeting in meetings:

        transcript = meeting.get("transcript")

        if not transcript:
            print(
                f"Skipping meeting {meeting['id']} - transcript is empty"
            )
            continue

        add_meeting_to_vector_db(
            meeting["id"],
            transcript
        )

        indexed_count += 1

    print(
        f"\nSuccessfully indexed {indexed_count} meeting(s)"
    )


def search_similar_meetings(query: str, k: int = 3):

    results = vector_store.similarity_search(
        query,
        k=k
    )

    return results


def search_meeting(query: str, meeting_id: int, k: int = 3):

    results = vector_store.similarity_search(
        query,
        k=k,
        filter={"meeting_id": meeting_id}
    )

    return results


def search_action_items(question: str):

    action_items = get_action_items()

    question_lower = question.lower()

    results = []

    for item in action_items:

        task = item["task"] or ""

        if any(
            word in task.lower()
            for word in question_lower.split()
            if len(word) > 3
        ):
            results.append(item)

    return results


def delete_meeting_from_vector_db(meeting_id: int):

    # Get all chunks belonging to this meeting
    results = vector_store.get(
        where={"meeting_id": meeting_id}
    )

    ids = results.get("ids", [])

    if ids:
        vector_store.delete(ids=ids)

    print(f"Meeting {meeting_id} deleted from ChromaDB")

