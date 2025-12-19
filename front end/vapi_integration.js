// VAPI Integration for Frontend
// Add this script to your homevisit.html

// 1. Include VAPI Web SDK
// <script src="https://unpkg.com/@vapi-ai/web"></script>

// 2. Initialize VAPI
const vapi = new Vapi("YOUR_VAPI_PUBLIC_KEY");

// 3. Handle VAPI events
vapi.on("call-start", () => {
    console.log("Call started");
    updateUI("Call connected. Speak now!");
});

vapi.on("speech-update", (speech) => {
    console.log("Speech update:", speech);
    displayTranscript(speech.transcript, speech.speaker);
});

vapi.on("message", (message) => {
    console.log("Message:", message);
    
    // Check if this is a compliance warning
    if (message.type === "function-call" && message.functionCall.name === "check_compliance") {
        const result = message.functionCall.result;
        if (result.warning) {
            displayComplianceWarning(result.warning, result.risk_level);
        }
    }
});

vapi.on("call-end", () => {
    console.log("Call ended");
    updateUI("Call ended");
});

// 4. UI Functions
function startCall() {
    // Start a call to your VAPI number
    vapi.start("YOUR_VAPI_PHONE_NUMBER");
}

function endCall() {
    vapi.stop();
}

function displayTranscript(text, speaker) {
    const transcriptDiv = document.getElementById('transcript');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${speaker}`;
    messageDiv.innerHTML = `
        <strong>${speaker}:</strong> ${text}
    `;
    transcriptDiv.appendChild(messageDiv);
    transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
}

function displayComplianceWarning(warning, riskLevel) {
    const warningDiv = document.getElementById('warnings');
    const warningItem = document.createElement('div');
    warningItem.className = `warning ${riskLevel}`;
    warningItem.innerHTML = `
        <div class="warning-icon">⚠️</div>
        <div class="warning-text">${warning}</div>
    `;
    warningDiv.appendChild(warningItem);
}

function updateUI(message) {
    document.getElementById('status').textContent = message;
}

// 5. Question prompts
function askQuestions(category) {
    // Trigger VAPI function to ask questions
    vapi.sendFunctionCall({
        name: "ask_questions",
        parameters: { category: category }
    });
}

// Example usage in HTML:
/*
<button onclick="startCall()">Start Housing Visit Call</button>
<button onclick="endCall()">End Call</button>

<div id="status">Ready to start call</div>

<div id="transcript">
    <h3>Conversation</h3>
</div>

<div id="warnings">
    <h3>Compliance Warnings</h3>
</div>

<div class="question-buttons">
    <button onclick="askQuestions('general')">General Questions</button>
    <button onclick="askQuestions('legal')">Legal Questions</button>
    <button onclick="askQuestions('building')">Building Questions</button>
</div>
*/
