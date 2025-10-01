#!/usr/bin/env python3
"""
Simple WebSocket server test to debug connection issues
"""

import asyncio
import websockets
import json
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def handle_connection(websocket, path):
    """Handle WebSocket connection"""
    print(f"🔌 New connection from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            print(f"📥 Received: {message}")
            
            try:
                data = json.loads(message)
                print(f"📋 Parsed data: {data}")
                
                # Echo back a response
                response = {
                    "type": "echo",
                    "original": data,
                    "timestamp": "2025-01-01T12:00:00Z"
                }
                
                await websocket.send(json.dumps(response))
                print(f"📤 Sent response: {response}")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON"
                }
                await websocket.send(json.dumps(error_response))
                
    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 Connection closed from {websocket.remote_address}")
    except Exception as e:
        print(f"❌ Error handling connection: {e}")

async def main():
    """Start the test WebSocket server"""
    print("🚀 Starting test WebSocket server on ws://localhost:8766")
    
    # Start server on a different port to avoid conflicts
    server = await websockets.serve(
        handle_connection,
        "localhost",
        8766,
        ping_interval=20,
        ping_timeout=10
    )
    
    print("✅ Test WebSocket server started on ws://localhost:8766")
    print("🔄 Server running... Press Ctrl+C to stop")
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test server stopped by user")
