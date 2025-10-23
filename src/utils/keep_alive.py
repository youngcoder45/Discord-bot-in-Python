"""
Keep-alive server for hosting platforms
Provides health endpoint and keeps the bot running on platforms like Railway, Render, etc.
"""

from flask import Flask
from threading import Thread
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask('')

@app.route('/')
def home():
    return "CodeVerse Bot is running! 🤖"

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "message": "Bot is running",
        "platform": os.getenv('HOSTING_PLATFORM', 'local')
    }

@app.route('/ping')
def ping():
    return "pong"

def run():
    """Run the Flask server"""
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    """Start the keep-alive server in a separate thread"""
    try:
        server = Thread(target=run)
        server.daemon = True
        server.start()
        logger.info(f"Health server started on port {os.getenv('PORT', 8080)}")
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
