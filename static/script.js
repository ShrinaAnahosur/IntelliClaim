document.addEventListener("DOMContentLoaded", function () {
    const chatContainer = document.getElementById("chat-container");
    const chatToggle = document.getElementById("chat-toggle");
    const closeChat = document.getElementById("close-chat");
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");

    // Toggle chat visibility
    chatToggle.addEventListener("click", () => {
        chatContainer.classList.add("active"); // Show chat container
        chatToggle.style.display = "none"; // Hide toggle button
    });

    // Close chat
    closeChat.addEventListener("click", () => {
        chatContainer.classList.remove("active"); // Hide chat container
        chatToggle.style.display = "block"; // Show toggle button
    });

    // Send message
    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") sendMessage();
    });

    function sendMessage() {
        const userMessage = chatInput.value.trim();
        if (!userMessage) return;

        displayMessage(userMessage, "user");

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => displayMessage(data.response, "bot"))
        .catch(error => console.error("Chatbot error:", error));


        chatInput.value = "";
    }

    function displayMessage(message, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        messageDiv.innerText = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll to bottom
    }
});