from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from main import (
    ActionItem,
    MeetingAnalysis,
    analyze_meeting,
    extract_action_items,
    validate_action_items,
    generate_followups
)

from crud import save_meeting, get_meeting, get_all_meetings, get_action_items

class MeetingState(TypedDict):
    transcript: str
    analysis: MeetingAnalysis
    action_items: list[ActionItem]
    validation: str
    followups: str


def meeting_analysis_node(state: MeetingState):

    transcript = state["transcript"]

    analysis = analyze_meeting(transcript)

    return {
        "analysis": analysis
    }


def action_items_node(state: MeetingState):

    transcript = state["transcript"]

    action_items = extract_action_items(transcript)

    return {
        "action_items": action_items
    }


def validation_node(state: MeetingState):

    action_items = state["action_items"]

    validation = validate_action_items(action_items)

    return {
        "validation": validation
    }


def followup_node(state: MeetingState):

    action_items = state["action_items"]

    followups = generate_followups(action_items)

    return {
        "followups": followups
    }


def check_validation(state: MeetingState):

    validation = state["validation"]

    if "False" in validation:
        return "followup"

    return "end"

graph = StateGraph(MeetingState)

graph.add_node("meeting_analysis", meeting_analysis_node)
graph.add_node("action_items", action_items_node)
graph.add_node("validation", validation_node)
graph.add_node("followup", followup_node)

graph.add_edge(START, "meeting_analysis")
graph.add_edge("meeting_analysis", "action_items")
graph.add_edge("action_items", "validation")

graph.add_conditional_edges(
    "validation",
    check_validation,
    {
        "followup": "followup",
        "end": END
    }
)

graph.add_edge("followup", END)

meeting_graph = graph.compile()


if __name__ == "__main__":
     
    transcript = """
    Rahul: We need to complete the backend API by Friday.

    Priya: I'll handle the database integration.

    Sarthak: I'll prepare the dashboard by Monday.

    Rahul: We have decided to use PostgreSQL for the project.

    Priya: We should also have the first version ready for testing next week.
    """

    result = meeting_graph.invoke({
        "transcript": transcript
    })

    print("\nMEETING ANALYSIS")
    print(result["analysis"])

    print("\nACTION ITEMS")
    for item in result["action_items"]:
        print(item)

    print("\nVALIDATION")
    print(result["validation"])

    print("\nFOLLOW-UPS")
    print(result.get("followups", ""))

    meeting_id = save_meeting(
        transcript=transcript,
        analysis=result["analysis"],
        action_items=result["action_items"],
        validation=result["validation"],
        followups=result.get("followups", "")
    )

    print("\nMEETING SAVED")
    print("Meeting ID:", meeting_id)

    saved_meeting = get_meeting(meeting_id)

    print("\nSAVED MEETING FROM DATABASE")
    print(saved_meeting)

    print("\nALL MEETINGS")
    print(get_all_meetings())

    print("\nALL ACTION ITEMS")
    print(get_action_items())

    print("\nACTION ITEMS FOR CURRENT MEETING")
    print(get_action_items(meeting_id))