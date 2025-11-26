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
from pathlib import Path
from aiohttp import web
from websocket_handler import websocket_handler
from config import HOST, PORT, OUTPUT_DIR, validate_environment
import qrcode


async def index(request: web.Request) -> web.Response:
    """Serve the static `index.html` from the `static/` directory."""
    static_dir = Path(__file__).parent / 'static'
    index_file = static_dir / 'index.html'
    if not index_file.exists():
        return web.Response(text='Index file not found. Ensure `static/index.html` exists.', status=404)
    return web.FileResponse(index_file)

def create_app() -> web.Application:
    """
    Create and configure the web application.

    This function sets up the aiohttp application with all necessary routes
    and middleware.

    Returns:
        web.Application: The configured web application
    """
    app = web.Application()
    # Serve static assets from ./static at /static
    static_dir = Path(__file__).parent / 'static'
    if static_dir.exists():
        app.router.add_static('/static', str(static_dir), show_index=False)

    app.router.add_get('/', index)
    app.router.add_get('/ws', websocket_handler)
    # Keep previous audio static route for generated audio files
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
def logQRcode(url):
    print(f"🚀: {url}")
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.show()

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