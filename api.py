from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field, field_validator

from fastapi.encoders import jsonable_encoder

from graph import meeting_graph
from crud import (
    save_meeting,
    get_meeting,
    get_all_meetings,
    get_action_items
)
from redis_service import get_json, set_json

from rag_service import (
    add_meeting_to_vector_db,
    clear_rag_cache,
    clear_global_rag_cache
)

from rag_qa import answer_question, answer_meeting_question

app = FastAPI(
    title="AI Meeting Intelligence API",
    description="API for meeting analysis and task automation",
    version="1.0.0"
)


class MeetingRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=50000)

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, value):
        if not value.strip():
            raise ValueError("Transcript cannot be empty or contain only whitespace")
        return value.strip()
    
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        if not value.strip():
            raise ValueError("Question cannot be empty or contain only whitespace")
        return value.strip()

@app.get("/")
def root():
    return {
        "message": "AI Meeting Intelligence API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/meetings")
def create_meeting(request: MeetingRequest):

    result = meeting_graph.invoke({
        "transcript": request.transcript
    })

    meeting_id = save_meeting(
        transcript=request.transcript,
        analysis=result["analysis"],
        action_items=result["action_items"],
        validation=result["validation"],
        followups=result.get("followups", "")
    )

    add_meeting_to_vector_db(
        meeting_id,
        request.transcript
    )

    clear_rag_cache(meeting_id)
    clear_global_rag_cache()

    return {
        "message": "Meeting processed successfully",
        "meeting_id": meeting_id
    }

@app.get("/meetings/{meeting_id}")
def get_meeting_by_id(meeting_id: int):

    # 1. Check Redis first
    cache_key = f"meeting:{meeting_id}"

    cached_meeting = get_json(cache_key)

    if cached_meeting is not None:
        return cached_meeting

    # 2. If not in Redis, get from PostgreSQL
    meeting = get_meeting(meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    # 3. Convert SQLAlchemy object into JSON-compatible data
    meeting_data = jsonable_encoder(meeting)

    # 4. Store JSON-compatible data in Redis
    set_json(cache_key, meeting_data)

    # 5. Return the meeting
    return meeting

@app.get("/meetings")
def get_meetings():

    meetings = get_all_meetings()

    return {
        "meetings": meetings
    }

@app.post("/meetings/ask")
def ask_meeting_question(request: QuestionRequest):

    try:
        answer = answer_question(request.question)

        return {
            "question": request.question,
            "answer": answer
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process your question right now. Please try again later."
        )
@app.post("/meetings/ask")
def ask_meeting_question(request: QuestionRequest):

    answer = answer_question(request.question)

    return {
        "question": request.question,
        "answer": answer
    }

@app.post("/meetings/{meeting_id}/ask")
def ask_specific_meeting(
    request: QuestionRequest,
    meeting_id: int = Path(..., gt=0, le=1000000)
):

    meeting = get_meeting(meeting_id)

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    try:
        answer = answer_meeting_question(
            request.question,
            meeting_id
        )

        return {
            "meeting_id": meeting_id,
            "question": request.question,
            "answer": answer
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process your question right now. Please try again later."
        )

@app.get("/action-items")
def get_all_action_items():

    action_items = get_action_items()

    return {
        "action_items": action_items
    }

@app.get("/meetings/{meeting_id}/action-items")
def get_meeting_action_items(meeting_id: int):

    # 1. Create a Redis cache key
    cache_key = f"meeting:{meeting_id}:action_items"

    # 2. Check Redis first
    cached_action_items = get_json(cache_key)

    if cached_action_items is not None:
        return {
            "action_items": cached_action_items
        }

    # 3. If not in Redis, get from PostgreSQL
    action_items = get_action_items(meeting_id)

    # 4. Convert SQLAlchemy objects to JSON-compatible data
    action_items_data = jsonable_encoder(action_items)

    # 5. Save the result in Redis
    set_json(cache_key, action_items_data)

    # 6. Return the action items
    return {
        "action_items": action_items
    }