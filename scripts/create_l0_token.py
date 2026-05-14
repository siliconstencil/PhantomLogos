import os
import time


def create_token():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    token_path = os.path.join(project_root, "data", "snapshots", "L0_AUTH_TOKEN")

    os.makedirs(os.path.dirname(token_path), exist_ok=True)

    print("[SOVEREIGN] Requesting L0 Authorization...")
    with open(token_path, "w") as f:
        f.write(str(time.time()))

    print(f"[SUCCESS] L0_AUTH_TOKEN created at: {token_path}")
    print("[INFO] Window of authorization: 60 seconds.")
    print("[INFO] Guardian will allow modifications during this window.")


if __name__ == "__main__":
    create_token()
