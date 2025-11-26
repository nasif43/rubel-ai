let ws;
let recognition;
let connected = false;
let connectedRole = null;
let lastMessageKey = null;
let lastMessageTs = 0;

function addMessage(from, text, outgoing = false) {
    const container = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message ' + (outgoing ? 'outgoing' : 'incoming');
    const span = document.createElement('span');
    span.className = 'message-from';
    span.textContent = from;
    const p = document.createElement('p');
    p.textContent = text;
    div.appendChild(span);
    div.appendChild(p);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function connect() {
    const roleInput = document.querySelector('input[name="role"]:checked');
    if (!roleInput) {
        alert('Please select a role first');
        return;
    }
    const role = roleInput.value;

    // show spinner when attempting to connect
    showSpinner();
    console.log('[client] connect() called, role=', role);

    // Avoid reconnecting if already connected with same role
    if (ws && ws.readyState === WebSocket.OPEN && connected && connectedRole === role) {
        hideSpinner();
        return;
    }

    // If there's an open socket with different role, close it first
    if (ws && ws.readyState !== WebSocket.CLOSED) {
        try { ws.close(); } catch (e) { console.warn('Error closing socket', e); }
        // reset local state immediately so UI reflects reconnect attempt
        connected = false;
        connectedRole = null;
    }

    // choose ws or wss matching current page protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = protocol + '//' + window.location.host + '/ws';
    console.log('[client] opening websocket to', wsUrl);
    ws = new WebSocket(wsUrl);
    ws.onopen = function() {
        ws.send(JSON.stringify({role: role}));
        document.querySelector('.status-text').textContent = 'Connected as ' + role;
        connected = true;
        connectedRole = role;
        hideSpinner();
    };
    ws.onerror = function(ev) {
        console.error('[client] websocket error', ev);
        hideSpinner();
    };
    ws.onclose = function(ev) {
        console.warn('[client] websocket closed', ev);
        document.querySelector('.status-text').textContent = 'Disconnected';
        connected = false;
        connectedRole = null;
        // show single disconnect system message
        addMessage('System', 'Disconnected');
        hideSpinner();
    };
    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.error) {
                addMessage('Error', data.error, false);
            } else if (data.from && data.text) {
                // deduplicate repeated messages (simple heuristic)
                const key = `${data.from}::${data.text}`;
                const now = Date.now();
                if (key === lastMessageKey && (now - lastMessageTs) < 2000) {
                    // duplicate within 2s, ignore
                    return;
                }
                lastMessageKey = key;
                lastMessageTs = now;
                addMessage(data.from, data.text, false);
            }
        } catch (e) {
            console.error('Invalid message', e);
        }
    };
    // (onclose now set above to include event info)
}

function showSpinner() {
    const s = document.getElementById('spinner');
    if (s) { s.classList.remove('hidden'); s.setAttribute('aria-hidden', 'false'); }
}

function hideSpinner() {
    const s = document.getElementById('spinner');
    if (s) { s.classList.add('hidden'); s.setAttribute('aria-hidden', 'true'); }
}

function sendMessage() {
    const messageEl = document.getElementById('message');
    const message = messageEl.value.trim();
    if (ws && message) {
        ws.send(JSON.stringify({text: message}));
        addMessage('You', message, true);
        messageEl.value = '';
    }
}

function startVoice() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
        return;
    }
    if (!recognition) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onstart = function() {
            document.querySelector('.status-text').textContent = 'Listening...';
        };
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('message').value = transcript;
            document.querySelector('.status-text').textContent = 'Captured: "' + transcript + '" - Sending...';
            sendMessage();
        };
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            let errorMessage = 'Speech recognition error: ' + event.error;
            if (event.error === 'not-allowed') {
                errorMessage = 'Microphone access denied. Please allow microphone access and try again.';
            } else if (event.error === 'no-speech') {
                errorMessage = 'No speech detected. Please try again.';
            } else if (event.error === 'network') {
                errorMessage = 'Network error. Please check your connection.';
            }
            document.querySelector('.status-text').textContent = errorMessage;
        };
        recognition.onend = function() {
            document.querySelector('.status-text').textContent = '';
        };
    }
    try { recognition.start(); } catch (e) { document.querySelector('.status-text').textContent = 'Error starting speech recognition: ' + e.message; }
}

function stopVoice() {
    if (recognition) {
        recognition.stop();
        document.querySelector('.status-text').textContent = 'Speech recognition stopped.';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // connect button removed — auto-connect on role select is used
    const form = document.getElementById('chat-form');
    const voiceBtn = document.getElementById('voiceBtn');
    const roleInputs = document.querySelectorAll('input[name="role"]');

    if (form) form.addEventListener('submit', (e) => { e.preventDefault(); sendMessage(); });
    if (voiceBtn) voiceBtn.addEventListener('click', startVoice);
    if (roleInputs && roleInputs.length) {
        roleInputs.forEach(r => r.addEventListener('change', () => {
            // auto-connect when role selected
            try { connect(); } catch (e) { console.error('Auto-connect failed', e); }
        }));
    }

    // Auto-connect if a role is already selected on load
    const preselected = document.querySelector('input[name="role"]:checked');
    if (preselected) {
        console.log('[client] preselected role found, auto-connecting', preselected.value);
        try { connect(); } catch (e) { console.error('Auto-connect on load failed', e); }
    }
});
