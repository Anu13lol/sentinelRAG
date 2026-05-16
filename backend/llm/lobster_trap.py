import subprocess
import json
import urllib.request
from urllib.error import URLError

# Configuration for the hardware proxy interface
LOBSTER_TRAP_CLI = "./lobstertrap.exe"
PROXY_URL = "http://localhost:8080/_lobstertrap/"

def inspect_prompt(prompt: str) -> dict:
    """
    Executes the Lobster Trap CLI to analyze a prompt before execution.
    Returns parsed JSON metadata regarding security risks.
    """
    try:
        # Execute the binary and capture standard output
        result = subprocess.run(
            [LOBSTER_TRAP_CLI, "inspect", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        
        metadata = json.loads(result.stdout) #json parsing
        return metadata

    except subprocess.CalledProcessError as e:
        print(f"CLI Execution Error: {e.stderr}")
        return {"risk_score": 0.0, "contains_injection_patterns": False, "error": "CLI execution failed"}
    except json.JSONDecodeError:
        print("Failed to parse Lobster Trap CLI output.")
        return {"risk_score": 0.0, "contains_injection_patterns": False, "error": "JSON parse error"}
    except FileNotFoundError:
        print(f"Lobster Trap binary not found at {LOBSTER_TRAP_CLI}.")
        return {"risk_score": 0.0, "contains_injection_patterns": False, "error": "Binary missing"}

def is_high_risk(prompt: str, threshold: float = 0.6) -> bool:
    """
    Evaluates if a prompt exceeds the acceptable risk threshold.
    """
    metadata = inspect_prompt(prompt)
    
    # Safe fallback if inspection fails
    risk_score = metadata.get("risk_score", 0.0)
    
    return risk_score > threshold

def get_lobster_trap_status() -> bool:
    """
    Checks if the Lobster Trap proxy is actively listening.
    Crucial for pre-flight validation during app startup.
    """
    try:
        # 2-second timeout prevents the backend from hanging if the proxy is down
        response = urllib.request.urlopen(PROXY_URL, timeout=2)
        return response.getcode() == 200
    except (URLError, TimeoutError):
        return False