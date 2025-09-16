#!/usr/bin/env python3
"""
Server launcher script for Multishot multiplayer game
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import GameServer

if __name__ == "__main__":
    print("=" * 50)
    print("MULTISHOT MULTIPLAYER SHOOTER - SERVER")
    print("=" * 50)
    print()

    host = input("Enter server host (default: localhost): ").strip()
    if not host:
        host = "localhost"

    port_str = input("Enter server port (default: 5555): ").strip()
    if not port_str:
        port = 5555
    else:
        try:
            port = int(port_str)
        except ValueError:
            print("Invalid port number, using default 5555")
            port = 5555

    print(f"\nStarting server on {host}:{port}")
    print("Press Ctrl+C to stop the server")
    print("-" * 30)

    server = GameServer(host, port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()