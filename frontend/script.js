
const API_BASE_URL = "http://127.0.0.1:8000";

// Load meetings from FastAPI
async function loadMeetings() {
    const response = await fetch(`${API_BASE_URL}/meetings`);

    if (!response.ok) {
        throw new Error("Failed to load meetings.");
    }

    const data = await response.json();
    return data.meetings || [];
}

// Load action items from FastAPI
async function loadActionItems() {
    const response = await fetch(`${API_BASE_URL}/action-items`);

    if (!response.ok) {
        throw new Error("Failed to load action items.");
    }

    const data = await response.json();
    return data.action_items || [];
}

// Display the latest meetings
function displayRecentMeetings(meetings) {
    const container = document.getElementById("recent-meetings");

    if (meetings.length === 0) {
        container.className = "empty-state";
        container.innerHTML = `
            <div class="empty-icon">▤</div>
            <h3>No meetings yet</h3>
            <p>Create your first meeting to see it here.</p>
        `;
        return;
    }

    container.className = "meeting-list";

    const recentMeetings = [...meetings]
        .reverse()
        .slice(0, 5);

    container.innerHTML = recentMeetings.map(meeting => `
        <article class="meeting-row">
            <div class="meeting-row-icon">▤</div>

            <div class="meeting-row-details">
                <h4>Meeting #${meeting.id}</h4>
                <p>${escapeHTML(
                    meeting.summary || "No summary available."
                )}</p>
                <span class="meeting-date">
                    ${escapeHTML(
                        meeting.created_at || "Date unavailable"
                    )}
                </span>
            </div>
        </article>
    `).join("");
}

// Safely display text returned by the API
function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

// Load dashboard data
async function loadDashboard() {
    const meetingsElement = document.getElementById("total-meetings");
    const actionsElement = document.getElementById("total-actions");
    const meetingsContainer = document.getElementById("recent-meetings");

    meetingsElement.textContent = "…";
    actionsElement.textContent = "…";

    try {
        const [meetings, actionItems] = await Promise.all([
            loadMeetings(),
            loadActionItems()
        ]);

        meetingsElement.textContent = meetings.length;
        actionsElement.textContent = actionItems.length;

        displayRecentMeetings(meetings);
    } catch (error) {
        console.error("Dashboard loading error:", error);

        meetingsElement.textContent = "—";
        actionsElement.textContent = "—";

        meetingsContainer.className = "empty-state";
        meetingsContainer.innerHTML = `
            <div class="empty-icon">!</div>
            <h3>Unable to load dashboard data</h3>
            <p>
                Make sure FastAPI is running at
                127.0.0.1:8000, then click Refresh.
            </p>
        `;
    }
}

// Refresh dashboard when the button is clicked
document
    .getElementById("refresh-button")
    .addEventListener("click", loadDashboard);

// Load data when the page opens
loadDashboard();


const pageTitles = {
    dashboard: "Overview",
    meetings: "Meetings",
    actions: "Action Items",
    assistant: "AI Assistant"
};

function showPage(pageName) {
    // Hide every page
    document.querySelectorAll(".page-view").forEach(page => {
        page.classList.remove("active");
    });

    // Show the selected page
    const selectedPage = document.getElementById(
        `${pageName}-page`
    );

    if (!selectedPage) {
        return;
    }

    selectedPage.classList.add("active");

    // Update the top heading
    document.getElementById("page-title").textContent =
        pageTitles[pageName];

    // Highlight the selected sidebar button
    document.querySelectorAll(".nav-item").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.page === pageName
        );
    });
}

// Connect all sidebar buttons
document.querySelectorAll(".nav-item").forEach(button => {
    button.addEventListener("click", () => {
        showPage(button.dataset.page);
    });
});


const meetingForm = document.getElementById("meeting-form");
const meetingMessage = document.getElementById("meeting-message");
const analyzeButton = document.getElementById("analyze-button");
const meetingsList = document.getElementById("meetings-list");

// Show a success or error message
function showMeetingMessage(message, type) {
    meetingMessage.textContent = message;
    meetingMessage.className = `message-box ${type}`;
    meetingMessage.hidden = false;
}

// Load meeting history
async function loadMeetingHistory() {
    meetingsList.innerHTML =
        '<p class="loading-text">Loading meetings...</p>';

    try {
        const meetings = await loadMeetings();

        if (meetings.length === 0) {
            meetingsList.innerHTML =
                '<p class="loading-text">No meetings found.</p>';
            return;
        }

        meetingsList.innerHTML = [...meetings]
            .reverse()
            .map(meeting => `
                <article class="meeting-row">
                    <div class="meeting-row-icon">▤</div>

                    <div class="meeting-row-details">
                        <h4>Meeting #${escapeHTML(meeting.id)}</h4>

                        <p class="meeting-summary">
                            ${escapeHTML(
                                meeting.summary || "No summary available."
                            )}
                        </p>

                        <span class="meeting-date">
                            ${escapeHTML(
                                meeting.created_at || "Date unavailable"
                            )}
                        </span>
                    </div>
                </article>
            `)
            .join("");
    } catch (error) {
        console.error("Meeting history error:", error);

        meetingsList.innerHTML =
            '<p class="loading-text">Could not load meeting history. Check the FastAPI server.</p>';
    }
}

// Submit a new meeting transcript
meetingForm.addEventListener("submit", async event => {
    event.preventDefault();

    const transcript = document
        .getElementById("transcript")
        .value
        .trim();

    if (!transcript) {
        showMeetingMessage("Please enter a meeting transcript.", "error");
        return;
    }

    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analyzing...";
    meetingMessage.hidden = true;

    try {
        const response = await fetch(`${API_BASE_URL}/meetings`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ transcript })
        });

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                result.detail || result.message || "Meeting creation failed."
            );
        }

        showMeetingMessage(
            `Meeting processed successfully! Meeting ID: ${
                result.meeting_id ?? result.id ?? "Created"
            }`,
            "success"
        );

        meetingForm.reset();

        await loadMeetingHistory();
        await loadDashboard();
    } catch (error) {
        console.error("Create meeting error:", error);

        showMeetingMessage(
            error.message || "Could not create the meeting. Check FastAPI.",
            "error"
        );
    } finally {
        analyzeButton.disabled = false;
        analyzeButton.textContent = "Analyze Meeting";
    }
});

// Refresh meeting history
document
    .getElementById("meetings-refresh-button")
    .addEventListener("click", loadMeetingHistory);

// Load history when the Meetings page is opened
document
    .querySelector('[data-page="meetings"]')
    .addEventListener("click", loadMeetingHistory);

// Initial load
loadMeetingHistory();


const actionItemsBody = document.getElementById("action-items-body");
const meetingFilter = document.getElementById("meeting-filter");

let allActionItems = [];

// Display action items in the table
function displayActionItems(items) {
    if (items.length === 0) {
        actionItemsBody.innerHTML = `
            <tr>
                <td colspan="4" class="table-message">
                    No action items found for this selection.
                </td>
            </tr>
        `;
        return;
    }

    actionItemsBody.innerHTML = items.map(item => `
        <tr>
            <td>${escapeHTML(item.task || "Untitled task")}</td>
            <td>${escapeHTML(item.assigned_to || "Not assigned")}</td>
            <td>${escapeHTML(item.deadline || "Not specified")}</td>
            <td>#${escapeHTML(item.meeting_id)}</td>
        </tr>
    `).join("");
}

// Apply the selected meeting filter
function filterActionItems() {
    const selectedMeeting = meetingFilter.value;

    const filteredItems = selectedMeeting === "all"
        ? allActionItems
        : allActionItems.filter(
            item => String(item.meeting_id) === selectedMeeting
        );

    displayActionItems(filteredItems);
}

// Load tasks from FastAPI
async function loadActionItemsPage() {
    actionItemsBody.innerHTML = `
        <tr>
            <td colspan="4" class="table-message">
                Loading action items...
            </td>
        </tr>
    `;

    try {
        allActionItems = await loadActionItems();

        document.getElementById("action-count").textContent =
            allActionItems.length;

        document.getElementById("assigned-count").textContent =
            allActionItems.filter(item => item.assigned_to).length;

        const meetingIds = [...new Set(
            allActionItems.map(item => String(item.meeting_id))
        )].sort((a, b) => Number(b) - Number(a));

        meetingFilter.innerHTML =
            '<option value="all">All Meetings</option>';

        meetingIds.forEach(id => {
            const option = document.createElement("option");
            option.value = id;
            option.textContent = `Meeting #${id}`;
            meetingFilter.appendChild(option);
        });

        filterActionItems();
    } catch (error) {
        console.error("Action items loading error:", error);

        actionItemsBody.innerHTML = `
            <tr>
                <td colspan="4" class="table-message">
                    Could not load action items. Check the FastAPI server.
                </td>
            </tr>
        `;
    }
}

meetingFilter.addEventListener("change", filterActionItems);

document
    .getElementById("actions-refresh-button")
    .addEventListener("click", loadActionItemsPage);

document
    .querySelector('[data-page="actions"]')
    .addEventListener("click", loadActionItemsPage);

// Initial load
loadActionItemsPage();


const questionForm = document.getElementById("question-form");
const questionScope = document.getElementById("question-scope");
const specificMeetingField = document.getElementById(
    "specific-meeting-field"
);
const questionMeetingId = document.getElementById("question-meeting-id");
const questionInput = document.getElementById("question-input");
const askButton = document.getElementById("ask-button");
const answerPanel = document.getElementById("answer-panel");
const answerMessage = document.getElementById("answer-message");

// Load available meeting IDs
async function loadQuestionMeetingOptions() {
    try {
        const meetings = await loadMeetings();

        if (meetings.length === 0) {
            questionMeetingId.innerHTML =
                '<option value="">No meetings available</option>';
            return;
        }

        questionMeetingId.innerHTML = [...meetings]
            .reverse()
            .map(meeting => `
                <option value="${escapeHTML(meeting.id)}">
                    Meeting #${escapeHTML(meeting.id)}
                </option>
            `)
            .join("");
    } catch (error) {
        console.error("Could not load meeting options:", error);

        questionMeetingId.innerHTML =
            '<option value="">Could not load meetings</option>';
    }
}

// Show or hide the meeting ID selector
questionScope.addEventListener("change", () => {
    specificMeetingField.hidden = questionScope.value !== "specific";
});

// Submit a question to the RAG API
questionForm.addEventListener("submit", async event => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
        answerMessage.textContent = "Please enter a question.";
        answerMessage.className = "message-box error";
        answerMessage.hidden = false;
        return;
    }

    let url = `${API_BASE_URL}/meetings/ask`;
    let scopeLabel = "Across all meetings";

    if (questionScope.value === "specific") {
        const meetingId = questionMeetingId.value;

        if (!meetingId) {
            answerMessage.textContent = "Please select a meeting.";
            answerMessage.className = "message-box error";
            answerMessage.hidden = false;
            return;
        }

        url = `${API_BASE_URL}/meetings/${encodeURIComponent(meetingId)}/ask`;
        scopeLabel = `Meeting #${meetingId}`;
    }

    askButton.disabled = true;
    askButton.textContent = "Searching...";
    answerMessage.hidden = true;
    answerPanel.hidden = true;

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                result.detail || result.message || "Question request failed."
            );
        }

        document.getElementById("answer-text").textContent =
            result.answer || "No answer was returned.";

        document.getElementById("answer-scope-label").textContent =
            scopeLabel;

        answerPanel.hidden = false;
    } catch (error) {
        console.error("AI assistant error:", error);

        answerMessage.textContent =
            error.message || "Could not process your question.";

        answerMessage.className = "message-box error";
        answerMessage.hidden = false;
    } finally {
        askButton.disabled = false;
        askButton.textContent = "Ask Assistant";
    }
});

// Load meeting options when the assistant page is opened
document
    .querySelector('[data-page="assistant"]')
    .addEventListener("click", loadQuestionMeetingOptions);

// Load options on initial page load
loadQuestionMeetingOptions();
