import threading
import time
import sys
from bridge.server import BridgeServer

def start_bridge():
    server = BridgeServer()
    server.start()
    return server



if __name__ == "__main__":
    print("--- JIET Studio Launcher Prototype ---")
    
    # 1. Start the Bridge (The Brain)
    print("[1/2] Starting Bridge Server...")
    bridge = start_bridge()
    time.sleep(1) # Give it a moment to bind

    # 2. Run the Factory (Blender) - REMOVED

    
    print("--- Test Complete. Shutting down. ---")
    bridge.stop()
    sys.exit(0)
