#!/usr/bin/env python3
"""
Generate a session token for testing
"""

import sys
sys.path.append('.')

from mcp_server.main import start_snap_session

def main():
    try:
        result = start_snap_session('test_user_new')
        print(f"✅ New session created!")
        print(f"🔑 Token: {result['display_token']}")
        print(f"📋 Session ID: {result['session_id']}")
        print(f"⏰ Valid for 30 minutes")
    except Exception as e:
        print(f"❌ Error generating token: {e}")

if __name__ == "__main__":
    main()
