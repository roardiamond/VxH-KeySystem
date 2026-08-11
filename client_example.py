"""
Yeh example code hai — isko apne sensitivityboost.py mein integrate karna hai.

Steps:
1. API_URL ko apne deployed key system ke URL se replace karo
2. check_key() function ko use karo paid features unlock karne se pehle
"""

import requests
import json
import os

# ========== CONFIG ========== 
# Apna deployed Key System URL yahan daalo (Render / Railway ka URL)
API_URL = "https://your-app-name.onrender.com/api/validate"

# Local storage for saved key (optional)
KEY_FILE = os.path.expanduser("~/.vxh_key")

def save_key(key: str):
    with open(KEY_FILE, "w") as f:
        f.write(key.strip())

def load_key() -> str:
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            return f.read().strip()
    return ""

def check_key(key: str = None) -> dict:
    """
    Key validate karta hai.
    Returns: {"valid": True/False, "message": "...", "expires_at": "..."}
    """
    if key is None:
        key = load_key()

    if not key:
        return {"valid": False, "message": "No key provided"}

    try:
        resp = requests.post(
            API_URL,
            json={"key": key},
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        data = resp.json()
        return data
    except Exception as e:
        return {"valid": False, "message": f"Connection error: {e}"}


# ========== EXAMPLE USAGE IN MENU ========== 
"""
Apne sensitivityboost.py ke main() ya menu mein aise use karo:

def unlock_paid_feature():
    print("\\033[93m[*] Checking license key...\\033[0m")
    
    # Pehle saved key try karo
    result = check_key()
    
    if not result.get("valid"):
        # Key nahi mili ya invalid → user se maango
        key = input("\\033[96mEnter your VxH Key: \\033[0m").strip()
        result = check_key(key)
        
        if result.get("valid"):
            save_key(key)
            print(f"\\033[92m[+] Key Valid! Expires: {result.get('expires_at')}\\033[0m")
        else:
            print(f"\\033[91m[!] {result.get('message')}\\033[0m")
            input("Press Enter...")
            return False
    else:
        print(f"\\033[92m[+] License active till: {result.get('expires_at')}\\033[0m")
    
    return True


# Phir paid options mein:
elif choice == "02":
    if unlock_paid_feature():
        # yahan paid feature ka code
        print("ESP Enabled (demo)")
    else:
        print("Key required for this feature")
"""

if __name__ == "__main__":
    # Quick test
    print("Testing key validation...")
    key = input("Enter key to test: ").strip()
    result = check_key(key)
    print(json.dumps(result, indent=2))
