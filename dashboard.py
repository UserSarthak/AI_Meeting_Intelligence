import streamlit as st
import requests

# Configure the dashboard page
st.set_page_config(
    page_title="AI Meeting Intelligence",
    page_icon="🤖",
    layout="wide"
)

# Dashboard title
st.title("🤖 AI Meeting Intelligence & Task Automation")
st.write(
    "Analyze meeting transcripts, review decisions, "
    "track action items, and ask questions about meetings."
)

# Sidebar navigation
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choose a page",
    [
        "Dashboard",
        "Meetings",
        "Action Items",
        "Ask Questions"
    ]
)

# Display the selected page

if page == "Dashboard":
    st.header("Dashboard")

    try:
        response = requests.get(
            "http://127.0.0.1:8000/meetings",
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        meetings = data.get("meetings", [])

        st.metric("Total Meetings", len(meetings))

        st.subheader("Recent Meetings")

        if meetings:
            for meeting in reversed(meetings[-5:]):
                with st.expander(
                    f"Meeting {meeting['id']}"
                ):
                    st.write("**Summary:**")
                    st.write(meeting.get("summary", "No summary available"))

                    st.write("**Created At:**")
                    st.write(meeting.get("created_at", "Unknown"))

        else:
            st.info("No meetings found.")

    except requests.RequestException as error:
        st.error(
            "Could not connect to the FastAPI backend. "
            "Make sure the API server is running."
        )
        st.caption(str(error))



elif page == "Meetings":
    st.header("Meetings")

    with st.expander("Create a New Meeting"):
        with st.form("create_meeting_form"):
            transcript = st.text_area(
                "Meeting Transcript",
                placeholder=(
                    "Example: Rahul will complete the backend API "
                    "by Friday. Priya will handle database integration."
                ),
                height=180
            )

            submitted = st.form_submit_button(
                "Analyze and Save Meeting"
            )

            if submitted:
                if not transcript.strip():
                    st.warning("Please enter a meeting transcript.")
                else:
                    try:
                        with st.spinner(
                            "Analyzing and saving the meeting..."
                        ):
                            response = requests.post(
                                "http://127.0.0.1:8000/meetings",
                                json={"transcript": transcript.strip()},
                                timeout=120
                            )
                            response.raise_for_status()
                            result = response.json()

                        st.success(
                            "Meeting processed successfully!"
                        )
                        st.json(result)

                    except requests.RequestException as error:
                        st.error(
                            "Could not create the meeting. "
                            "Check the FastAPI server and try again."
                        )
                        st.caption(str(error))

    try:
        response = requests.get(
            "http://127.0.0.1:8000/meetings",
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        meetings = data.get("meetings", [])

        if not meetings:
            st.info("No meetings found.")

        else:
            for meeting in reversed(meetings):
                with st.expander(
                    f"Meeting {meeting['id']} — "
                    f"{meeting.get('created_at', 'Unknown date')}"
                ):
                    st.subheader("Summary")
                    st.write(meeting.get("summary", "No summary available"))

                    st.subheader("Transcript")
                    st.text(meeting.get("transcript", "No transcript available"))

                    st.subheader("Validation")
                    st.markdown(
                        meeting.get("validation", "No validation available")
                    )

                    st.subheader("Follow-up Questions")
                    st.markdown(
                        meeting.get("followups", "No follow-ups available")
                    )

    except requests.RequestException as error:
        st.error("Could not connect to the FastAPI backend.")
        st.caption(str(error))



elif page == "Action Items":
    st.header("Action Items")

    try:
        response = requests.get(
            "http://127.0.0.1:8000/action-items",
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        action_items = data.get("action_items", [])

        if not action_items:
            st.info("No action items found.")

        else:
            st.metric("Total Action Items", len(action_items))

            # Filter action items by meeting
            meeting_ids = sorted({
                item["meeting_id"] for item in action_items
            })

            selected_meeting = st.selectbox(
                "Filter by Meeting",
                ["All Meetings"] + meeting_ids
            )

            if selected_meeting != "All Meetings":
                filtered_items = [
                    item for item in action_items
                    if item["meeting_id"] == selected_meeting
                ]
            else:
                filtered_items = action_items

            st.subheader("Task List")

            for item in filtered_items:
                with st.expander(
                    f"Task {item['id']}: {item['task']}"
                ):
                    st.write(
                        f"**Meeting ID:** {item['meeting_id']}"
                    )
                    st.write(
                        f"**Assigned To:** "
                        f"{item.get('assigned_to') or 'Not assigned'}"
                    )
                    st.write(
                        f"**Deadline:** "
                        f"{item.get('deadline') or 'Not specified'}"
                    )

    except requests.RequestException as error:
        st.error("Could not connect to the FastAPI backend.")
        st.caption(str(error))


elif page == "Ask Questions":
    st.header("Ask Questions")
    st.write(
        "Ask questions about all meetings or a specific meeting."
    )

    scope = st.radio(
        "Search scope",
        ["All Meetings", "Specific Meeting"],
        horizontal=True
    )

    meeting_id = None

    if scope == "Specific Meeting":
        meeting_id = st.number_input(
            "Meeting ID",
            min_value=1,
            max_value=1000000,
            value=9,
            step=1
        )

    question = st.text_area(
        "Enter your question",
        placeholder="Example: Who is responsible for preparing the dashboard?"
    )

    if st.button("Ask Question", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")

        else:
            if scope == "All Meetings":
                url = "http://127.0.0.1:8000/meetings/ask"
            else:
                url = (
                    f"http://127.0.0.1:8000/meetings/"
                    f"{int(meeting_id)}/ask"
                )

            try:
                with st.spinner("Searching meeting information..."):
                    response = requests.post(
                        url,
                        json={"question": question.strip()},
                        timeout=60
                    )
                    response.raise_for_status()
                    result = response.json()

                st.subheader("Answer")
                st.write(
                    result.get("answer", "No answer was returned.")
                )

            except requests.RequestException as error:
                st.error(
                    "The question could not be processed. "
                    "Check that FastAPI is running and the request is valid."
                )
                st.caption(str(error))

