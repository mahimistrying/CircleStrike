#!/usr/bin/env python3
"""
Client launcher script for Multishot multiplayer game
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import MultiplayerClient

if __name__ == "__main__":
    print("=" * 50)
    print("MULTISHOT MULTIPLAYER SHOOTER - CLIENT")
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

    print(f"\nConnecting to {host}:{port}")
    print("-" * 30)

    client = MultiplayerClient(host, port)

    if not client.connect():
        print("Failed to connect to server!")
        print("Make sure the server is running and the address is correct.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("Connected! Starting game...")
    client.run()