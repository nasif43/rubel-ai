"""
Server module for Rubel AI Chat Application.

This module sets up and runs the web server including:
- Route configuration
- Static file serving
- Server lifecycle management
- HTML page serving
"""
import asyncio
import socket
from aiohttp import web
from websocket_handler import websocket_handler
from config import HOST, PORT, OUTPUT_DIR, validate_environment
import qrcode

async def index(request: web.Request) -> web.Response:
    """
    Serve the HTML page for the chat interface.

    This function returns the main HTML page that provides the user interface
    for connecting to the chat application via WebSocket.

    Args:
        request (web.Request): The HTTP request

    Returns:
        web.Response: The HTML response
    """
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Rubel Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
        input, button { margin: 5px; padding: 8px; }
        select { margin: 5px; padding: 8px; }
        #stopAudioBtn { background-color: #ff4444; color: white; border: none; border-radius: 4px; }
        #stopAudioBtn:hover { background-color: #cc0000; }
    </style>
</head>
<body>
    <h1>Rubel AI Chat</h1>
    <p>Select your role and start chatting!</p>
    <select id="role">
        <option value="mim">Mim</option>
        <option value="joker">Joker</option>
        <option value="spec_actor">Spec Actor</option>
    </select>
    <button onclick="connect()">Connect</button>
    <br><br>
    <input type="text" id="message" placeholder="Type your message or use voice" onkeypress="if(event.key=='Enter') sendMessage()">
    <button onclick="sendMessage()">Send</button>
    <button onclick="startVoice()">🎤 Speak</button>
    <button onclick="stopVoice()">Stop Recording</button>
    <br>
    <div id="status"></div>
    <br>
    <div id="messages"></div>
    <script>
        let ws;
        let recognition;
        function connect() {
            const role = document.getElementById('role').value;
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            ws.onopen = function() {
                ws.send(JSON.stringify({role: role}));
                document.getElementById('messages').innerHTML += '<p>Connected as ' + role + '</p>';
            };
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.error) {
                    document.getElementById('messages').innerHTML += '<p>Error: ' + data.error + '</p>';
                } else if (data.from && data.text) {
                    document.getElementById('messages').innerHTML += '<p><strong>' + data.from + ':</strong> ' + data.text + '</p>';
                }
                document.getElementById('status').innerHTML = '';
            };
            ws.onclose = function() {
                document.getElementById('messages').innerHTML += '<p>Disconnected</p>';
            };
        }
        function sendMessage() {
            const message = document.getElementById('message').value;
            if (ws && message) {
                ws.send(JSON.stringify({text: message}));
                document.getElementById('message').value = '';
            }
        }
        function startVoice() {
            // Check if speech recognition is supported
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
                    document.getElementById('status').innerHTML = 'Listening... Speak now.';
                };
                
                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('message').value = transcript;
                    document.getElementById('status').innerHTML = 'Captured: "' + transcript + '" - Sending...';
                    sendMessage();
                };
                
                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                    let errorMessage = 'Speech recognition error: ' + event.error;
                    
                    // Provide helpful error messages
                    if (event.error === 'not-allowed') {
                        errorMessage = 'Microphone access denied. Please allow microphone access and try again.';
                    } else if (event.error === 'no-speech') {
                        errorMessage = 'No speech detected. Please try again.';
                    } else if (event.error === 'network') {
                        errorMessage = 'Network error. Please check your connection.';
                    }
                    
                    document.getElementById('status').innerHTML = errorMessage;
                };
                
                recognition.onend = function() {
                    document.getElementById('status').innerHTML = '';
                };
            }
            
            try {
                recognition.start();
            } catch (e) {
                document.getElementById('status').innerHTML = 'Error starting speech recognition: ' + e.message;
            }
        }
        function stopVoice() {
            if (recognition) {
                recognition.stop();
                document.getElementById('status').innerHTML = 'Speech recognition stopped.';
            }
        }
    </script>
</body>
</html>
    """
    return web.Response(text=html, content_type='text/html')

def create_app() -> web.Application:
    """
    Create and configure the web application.

    This function sets up the aiohttp application with all necessary routes
    and middleware.

    Returns:
        web.Application: The configured web application
    """
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/ws', websocket_handler)
    app.router.add_static('/audio', OUTPUT_DIR)
    return app

def get_local_ip() -> str:
    """
    Get the local IP address of this machine.

    Returns:
        str: The local IP address, or 'localhost' if unable to determine
    """
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to Google DNS
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "localhost"

async def run_server() -> None:
    """
    Run the web server.

    This function starts the server and runs it indefinitely until interrupted.
    It validates the environment before starting and handles graceful shutdown.
    """
    # Validate environment
    errors = validate_environment()
    if errors:
        for error in errors:
            print(f"Error: {error}")
        return

    app = create_app()

    local_ip = get_local_ip()
    print(f"Starting server on:")
    print(f"  Local: http://localhost:{PORT}")
    print(f"  Network: http://{local_ip}:{PORT}")
    print(f"Access from other devices on your network using: http://{local_ip}:{PORT}")
    clienturl = f"http://{local_ip}:{PORT}"
    logQRcode(clienturl)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()

    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down server...")
        await runner.cleanup()