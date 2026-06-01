import os
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.append(str(root))

print("==================================================")
print("     PHANTOM LOGOS WEB UI OPERATOR DASHBOARD      ")
print("==================================================")
print("[INFO] Initializing Web Console on port 8080...")
print("[INFO] URL: http://localhost:8080")
print("[INFO] Press Ctrl+C to terminate the console.")

try:
    server_path = os.path.join("src", "dashboard", "api_server.py")
    subprocess.run([sys.executable, server_path])
except KeyboardInterrupt:
    print("\n[INFO] Dashboard server stopped by operator.")
except Exception as e:
    print(f"\n[ERROR] Failed to launch dashboard: {e}")
