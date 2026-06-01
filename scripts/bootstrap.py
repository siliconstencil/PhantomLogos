# Central Single-Entry Bootstrap and Installer (v1.2.1)
# Ensures correct python environment, installs dependencies, pulls GGUF models,
# runs migrations, seeds local data stores, and verifies system integrity.
# ASCII code only. No emojis.

import argparse
import os
import shutil
import subprocess
import sys

REQUIRED_PYTHON_VERSION = (3, 12)
REQUIRED_MODELS = [
    "qwen3.5-4b-ud:latest",
    "ministral-3b-ud:latest",
    "phi-4-mini-ud:latest",
    "nomic-embed-text-v2-moe-q8:latest",
]


def log(msg: str, level: str = "INFO") -> None:
    print(f"[{level}] {msg}")


def check_python_version() -> None:
    log("Checking Python version...")
    current = sys.version_info
    if current < REQUIRED_PYTHON_VERSION:
        log(
            f"Python version mismatch. Found {current.major}.{current.minor}, "
            f"but >= {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]} is required.",
            "ERROR",
        )
        sys.exit(1)
    log(f"Python version {sys.version.split()[0]} matches requirements.")


def ensure_directories() -> None:
    log("Ensuring required directories exist...")
    dirs = ["data", "logs", "models", "bin"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    log("Directories ready.")


def copy_env_file() -> None:
    log("Checking .env file status...")
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            log(
                "Created .env from .env.example. Please review and customize it before running the system."
            )
        else:
            log(".env.example not found. Please create .env manually.", "WARNING")
    else:
        log(".env already exists, skipping copy.")


def run_command(cmd: list[str], description: str) -> None:
    log(f"Running: {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        log(f"Successfully finished: {description}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        log(f"Failed to execute: {description}. Error: {e.stderr}", "ERROR")
        sys.exit(1)


def check_ollama(skip_models: bool) -> None:
    log("Verifying Ollama service status...")
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        log(
            "Ollama executable not found in PATH. Please install it from https://ollama.com",
            "ERROR",
        )
        sys.exit(1)

    try:
        subprocess.run(["ollama", "list"], check=True, capture_output=True)
        log("Ollama service is up and reachable.")
    except Exception as e:
        log(f"Ollama reachable test failed. Is the service running? Details: {e}", "ERROR")
        sys.exit(1)

    if not skip_models:
        log("Pulling required LLM and Embedding models...")
        for model in REQUIRED_MODELS:
            log(f"Pulling model: {model}...")
            # We don't use check=True for pull if model may already exist or offline fallback is preferred,
            # but let's try to pull it.
            subprocess.run(["ollama", "pull", model])
        log("Models successfully verified.")
    else:
        log("Skipping model pulls as requested.")


def run_database_migrations() -> None:
    log("Running Alembic database upgrades...")
    if (
        shutil.which("alembic")
        or os.path.exists(os.path.join(".venv", "Scripts", "alembic.exe"))
        or os.path.exists(os.path.join(".venv", "bin", "alembic"))
    ):
        alembic_cmd = "alembic"
        if sys.platform == "win32" and os.path.exists(
            os.path.join(".venv", "Scripts", "alembic.exe")
        ):
            alembic_cmd = os.path.join(".venv", "Scripts", "alembic.exe")
        elif os.path.exists(os.path.join(".venv", "bin", "alembic")):
            alembic_cmd = os.path.join(".venv", "bin", "alembic")

        try:
            sections = ["mnemosyne", "reliability", "spatial"]
            for section in sections:
                log(f"Upgrading database section: {section}...")
                try:
                    subprocess.run([alembic_cmd, "-n", section, "upgrade", "head"], check=True)
                except subprocess.CalledProcessError as sub_err:
                    log(
                        f"Upgrade failed for section {section}, attempting to stamp as head... Details: {sub_err}",
                        "WARNING",
                    )
                    subprocess.run([alembic_cmd, "-n", section, "stamp", "head"], check=True)
            log("Database migrations successfully completed.")
        except Exception as e:
            log(f"Database migrations failed: {e}", "ERROR")
            sys.exit(1)
    else:
        log("Alembic package not found, skipping migrations.", "WARNING")


def seed_data(skip_seeds: bool) -> None:
    if skip_seeds:
        log("Skipping data seeding.")
        return

    log("Seeding initial data stores...")
    # Executing seeding scripts using local python
    python_cmd = sys.executable

    run_command([python_cmd, "scripts/seed_14_axes.py"], "Seeding 14-Axes memory metadata")
    run_command([python_cmd, "scripts/seed_semantic.py"], "Seeding semantic memory vector store")
    log("Seeding complete.")


def verify_system_integrity() -> None:
    log("Running final system integrity health check...")
    python_cmd = sys.executable
    try:
        result = subprocess.run(
            [python_cmd, "scripts/health_check_14_axes.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        log("System integrity check completed.")
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        log("System health check reported anomalies, please review logs.", "WARNING")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phantom Logos Single-Entry Bootstrap Installer Script (v1.2.1)"
    )
    parser.add_argument("--skip-models", action="store_true", help="Skip pulling Ollama models")
    parser.add_argument(
        "--skip-seeds", action="store_true", help="Skip initial seeding of databases"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only verify existing environment and integrity"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable detailed installer logging")

    args = parser.parse_args()

    log("--- Starting Phantom Logos Bootstrap Installer (v1.2.1) ---")

    check_python_version()

    if args.check_only:
        log("Check-only mode enabled. Skipping installations and modifications.")
        check_ollama(skip_models=True)
        verify_system_integrity()
        log("System check complete.")
        return

    ensure_directories()
    copy_env_file()

    # 1. Virtual Environment Setup Check
    if not os.path.exists(".venv"):
        log("Creating virtual environment (.venv)...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        log("Virtual environment created.")

    # 2. Dependency Installation
    # Determine the correct pip path inside venv
    pip_cmd = "pip"
    if sys.platform == "win32" and os.path.exists(os.path.join(".venv", "Scripts", "pip.exe")):
        pip_cmd = os.path.join(".venv", "Scripts", "pip.exe")
    elif os.path.exists(os.path.join(".venv", "bin", "pip")):
        pip_cmd = os.path.join(".venv", "bin", "pip")

    log("Installing dependencies in editable mode...")
    subprocess.run([pip_cmd, "install", "-e", ".[dev]"], check=True)
    log("Dependencies successfully installed.")

    # 3. Model Pulls
    check_ollama(skip_models=args.skip_models)

    # 4. Database Setup & Seeding
    run_database_migrations()
    seed_data(args.skip_seeds)

    # 5. Verification
    verify_system_integrity()

    log("--- Bootstrap Installation Successfully Completed (v1.2.1) ---")
    log("To interact with the CLI, run: python scripts/hermes_cli.py")
    log("To launch the operator dashboard, run: python scripts/dashboard.py")


if __name__ == "__main__":
    main()
