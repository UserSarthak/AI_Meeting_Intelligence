from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


class MeetingAnalysis(BaseModel):
    summary: str
    discussions: list[str]
    decisions: list[str]


class ActionItem(BaseModel):
    task: str
    assigned_to: Optional[str] = None
    deadline: Optional[str] = None


def analyze_meeting(transcript):

    prompt = f"""
Analyze the following meeting transcript.

Return the answer exactly in this format:

SUMMARY:
Write a concise summary.

DISCUSSIONS:
- Discussion 1
- Discussion 2
- Discussion 3

DECISIONS:
- Decision 1
- Decision 2

Rules:

- Discussions should contain the important topics, ideas, concerns,
  or points discussed.
- Decisions should contain only decisions that were explicitly agreed
  upon or finalized.
- Do not treat tasks, deadlines, suggestions, or commitments as decisions.
- Do not assume that a speaker is responsible for a task unless the
  transcript explicitly says so.

Meeting transcript:

{transcript}
"""

    result = llm.invoke(prompt)

    text = result.content

    sections = {
        "summary": "",
        "discussions": [],
        "decisions": []
    }

    current_section = None

    for line in text.splitlines():

        line = line.strip()

        if line == "SUMMARY:":
            current_section = "summary"

        elif line == "DISCUSSIONS:":
            current_section = "discussions"

        elif line == "DECISIONS:":
            current_section = "decisions"

        elif line:

            if current_section == "summary":
                sections["summary"] += line + " "

            elif current_section == "discussions":
                if line.startswith("-"):
                    sections["discussions"].append(
                        line[1:].strip()
                    )

            elif current_section == "decisions":
                if line.startswith("-"):
                    sections["decisions"].append(
                        line[1:].strip()
                    )

    return MeetingAnalysis(
        summary=sections["summary"].strip(),
        discussions=sections["discussions"],
        decisions=sections["decisions"]
    )


def extract_action_items(transcript):

    prompt = f"""
You are an action-item extraction system.

Your job is to carefully read the meeting transcript and identify
EVERY task, commitment, responsibility, or piece of work that someone
is expected to complete.

IMPORTANT:
A sentence describing a person doing something is an action item.

Examples:

"Rahul will complete the backend API by Friday."
→ Task: Complete the backend API
→ Assigned To: Rahul
→ Deadline: Friday

"Priya will handle the database integration."
→ Task: Handle the database integration
→ Assigned To: Priya
→ Deadline: None

"Sarthak will prepare the dashboard by Monday."
→ Task: Prepare the dashboard
→ Assigned To: Sarthak
→ Deadline: Monday

"Someone needs to prepare the documentation."
→ Task: Prepare the documentation
→ Assigned To: None
→ Deadline: None

Rules:

1. Extract ALL actual tasks, commitments, responsibilities, and work
   that someone is expected to perform.

2. If a person says they will do something, that person is responsible.

3. If a sentence explicitly says that a person needs to complete or
   handle something, assign that person.

4. If the responsible person cannot be determined, use None.

5. If a deadline is not mentioned, use None.

6. Do NOT create an action item for a decision alone.

7. Do NOT create an action item for a general discussion or suggestion
   unless someone is expected to perform an actual task.

8. Do not skip an action item because information is missing.

9. Return ALL action items.

10. Return ONLY the following format.

ACTION ITEMS:
- Task: <task> | Assigned To: <person or None> | Deadline: <deadline or None>

If there are no action items, return exactly:

ACTION ITEMS:
None

Meeting transcript:

{transcript}
"""

    result = llm.invoke(prompt)

    text = result.content

    print("\nRAW ACTION ITEM RESPONSE:")
    print(text)

    action_items = []

    for line in text.splitlines():

        line = line.strip()

        if not line.startswith("- Task:"):
            continue

        parts = line[2:].split("|")

        task = None
        assigned_to = None
        deadline = None

        for part in parts:

            part = part.strip()

            if part.startswith("Task:"):
                task = part.replace("Task:", "", 1).strip()

            elif part.startswith("Assigned To:"):
                assigned_to = part.replace("Assigned To:", "", 1).strip()

            elif part.startswith("Deadline:"):
                deadline = part.replace("Deadline:", "", 1).strip()

        if assigned_to in ["None", "none", "NULL", "null", ""]:
            assigned_to = None

        if deadline in ["None", "none", "NULL", "null", ""]:
            deadline = None

        if task:
            action_items.append(
                ActionItem(
                    task=task,
                    assigned_to=assigned_to,
                    deadline=deadline
                )
            )

    return action_items


def validate_action_items(action_items):

    prompt = f"""
Validate the following action items from a meeting.

For each action item check:

- Whether the task is clear
- Whether a responsible person is assigned
- Whether a deadline is specified

Return the result in the following format:

Valid: True or False

Issues:
- List each missing or unclear piece of information.

Action items:

{action_items}
"""
    result = llm.invoke(prompt)

    return result.content


def generate_followups(action_items):

    prompt = f"""
Based on the following action items, generate follow-up questions
for any missing information.

For each action item:

- If the responsible person is missing, ask who is responsible.
- If the deadline is missing, ask what the deadline is.
- Do not ask about information that is already available.

Action items:

{action_items}
"""

    result = llm.invoke(prompt)

    return result.content

if __name__ == "__main__":

    transcript = """
    Rahul will complete the backend API by Friday.
    Priya will handle the database integration.
    The team decided to use PostgreSQL as the database system.
    """

    action_items = extract_action_items(transcript)

    print("\nEXTRACTED ACTION ITEMS:")

    for item in action_items:
        print(item)


