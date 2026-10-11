from database import SessionLocal
from models import Meeting, Discussion, Decision, ActionItemDB


def save_meeting(
    transcript,
    analysis,
    action_items,
    validation,
    followups
):

    db = SessionLocal()

    try:

        meeting = Meeting(
            transcript=transcript,
            summary=analysis.summary,
            validation=validation,
            followups=followups
        )

        db.add(meeting)
        db.flush()

        for discussion in analysis.discussions:

            db.add(
                Discussion(
                    meeting_id=meeting.id,
                    discussion=discussion
                )
            )

        for decision in analysis.decisions:

            db.add(
                Decision(
                    meeting_id=meeting.id,
                    decision=decision
                )
            )

        for item in action_items:

            db.add(
                ActionItemDB(
                    meeting_id=meeting.id,
                    task=item.task,
                    assigned_to=item.assigned_to,
                    deadline=item.deadline
                )
            )

        db.commit()

        return meeting.id

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()

def get_meeting(meeting_id):

    db = SessionLocal()

    try:

        meeting = db.query(Meeting).filter(
            Meeting.id == meeting_id
        ).first()

        if not meeting:
            return None

        return {
            "id": meeting.id,
            "transcript": meeting.transcript,
            "summary": meeting.summary,
            "validation": meeting.validation,
            "followups": meeting.followups,
            "created_at": meeting.created_at,

            "discussions": [
                discussion.discussion
                for discussion in meeting.discussions
            ],

            "decisions": [
                decision.decision
                for decision in meeting.decisions
            ],

            "action_items": [
                {
                    "task": item.task,
                    "assigned_to": item.assigned_to,
                    "deadline": item.deadline
                }
                for item in meeting.action_items
            ]
        }

    finally:

        db.close()

def get_all_meetings():

    db = SessionLocal()

    try:

        meetings = db.query(Meeting).all()

        return [
            {
                "id": meeting.id,
                "transcript": meeting.transcript,
                "summary": meeting.summary,
                "validation": meeting.validation,
                "followups": meeting.followups,
                "created_at": meeting.created_at
            }
            for meeting in meetings
        ]

    finally:

        db.close()

def get_action_items(meeting_id=None):
    
    db = SessionLocal()

    try:

        query = db.query(ActionItemDB)

        if meeting_id is not None:
            query = query.filter(
                ActionItemDB.meeting_id == meeting_id
            )

        action_items = query.all()

        return [
            {
                "id": item.id,
                "meeting_id": item.meeting_id,
                "task": item.task,
                "assigned_to": item.assigned_to,
                "deadline": item.deadline
            }
            for item in action_items
        ]

    finally:

        db.close()
