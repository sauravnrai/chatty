"use strict";

let stompClient = null;
let currentName = "";
let connectionAttempt = 0;
let connectionTimer = null;
const byId = (id) => document.getElementById(id);

function feedback(id, message) {
    const element = byId(id);
    element.textContent = message;
    element.hidden = !message;
}

function connectionFailed(attempt) {
    if (attempt !== connectionAttempt) return;
    window.clearTimeout(connectionTimer);
    connectionAttempt += 1;
    byId("login").disabled = false;
    byId("login-status").textContent = "";
    if (byId("chat-room").hidden) {
        feedback("login-error", "Could not connect. Please try entering the chat again.");
        byId("login").focus();
    } else {
        byId("connection-status").textContent = "Connection lost";
        byId("send-btn").disabled = true;
        feedback("message-error", "Connection lost. Log out and enter again to reconnect.");
    }
    const client = stompClient;
    stompClient = null;
    if (client) {
        try { client.disconnect(); } catch (_) { /* UI remains usable if the socket is already closed. */ }
    }
}

function connect(name) {
    const attempt = ++connectionAttempt;
    byId("login").disabled = true;
    byId("login-status").textContent = "Connecting to the shared room…";
    feedback("login-error", "");
    connectionTimer = window.setTimeout(() => connectionFailed(attempt), 15000);
    try {
        const client = Stomp.over(new SockJS("/server1"));
        stompClient = client;
        client.debug = null;
        client.connect({}, () => {
            if (attempt !== connectionAttempt) {
                client.disconnect();
                return;
            }
            window.clearTimeout(connectionTimer);
            client.subscribe("/topic/return-to", (response) => {
                try { showMessage(JSON.parse(response.body)); }
                catch (_) { feedback("message-error", "A message could not be displayed. Please try again."); }
            });
            currentName = name;
            byId("name-title").textContent = `Signed in as ${name}`;
            byId("name-form").hidden = true;
            byId("chat-room").hidden = false;
            byId("login").disabled = false;
            byId("send-btn").disabled = false;
            byId("login-status").textContent = "";
            byId("connection-status").textContent = "Connected to the shared room";
            byId("message-value").focus();
        }, () => connectionFailed(attempt));
    } catch (_) {
        connectionFailed(attempt);
    }
}

function showMessage(message) {
    if (!message || typeof message.name !== "string" || typeof message.content !== "string") {
        throw new Error("Invalid message");
    }
    const log = byId("message-log");
    const nearBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 80;
    const item = document.createElement("li");
    item.className = "message-card";
    const author = document.createElement("p");
    author.className = "message-author";
    author.textContent = message.name;
    const content = document.createElement("p");
    content.className = "message-content";
    content.textContent = message.content;
    item.append(author, content);
    byId("message-list").append(item);
    byId("empty-state").hidden = true;
    if (nearBottom) log.scrollTop = log.scrollHeight;
}

function sendMessage() {
    const input = byId("message-value");
    const content = input.value.trim();
    if (!content || content.length > 2000) {
        input.setAttribute("aria-invalid", "true");
        feedback("message-error", "Enter a message between 1 and 2,000 characters.");
        input.focus();
        return;
    }
    input.removeAttribute("aria-invalid");
    feedback("message-error", "");
    if (!stompClient || !stompClient.connected) {
        feedback("message-error", "You are not connected. Log out and enter again to reconnect.");
        return;
    }
    try {
        stompClient.send("/chatty/message", {}, JSON.stringify({ name: currentName, content }));
        input.value = "";
        input.focus();
    } catch (_) {
        feedback("message-error", "Your message could not be sent. Please try again.");
        input.focus();
    }
}

byId("login-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (byId("login").disabled) return;
    const input = byId("name-value");
    const name = input.value.trim();
    if (!name || name.length > 80) {
        input.setAttribute("aria-invalid", "true");
        feedback("login-error", "Enter a display name between 1 and 80 characters.");
        input.focus();
        return;
    }
    input.removeAttribute("aria-invalid");
    connect(name);
});

byId("message-form").addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage();
});

byId("logout").addEventListener("click", () => {
    connectionAttempt += 1;
    window.clearTimeout(connectionTimer);
    const client = stompClient;
    stompClient = null;
    currentName = "";
    if (client) {
        try { client.disconnect(); } catch (_) { /* Always restore the login view. */ }
    }
    byId("chat-room").hidden = true;
    byId("name-form").hidden = false;
    byId("name-title").textContent = "";
    byId("message-list").replaceChildren();
    byId("empty-state").hidden = false;
    byId("message-value").value = "";
    byId("message-value").removeAttribute("aria-invalid");
    byId("connection-status").textContent = "Not connected";
    byId("login").disabled = false;
    feedback("login-error", "");
    feedback("message-error", "");
    byId("name-value").focus();
});
