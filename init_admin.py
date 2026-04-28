#!/usr/bin/env python3
"""初始化 admin 账户"""
import json, os, sys, bcrypt
from datetime import datetime

USERS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "users.json")

def main():
    password = sys.argv[1] if len(sys.argv) > 1 else "admin123!"
    if len(password) < 8:
        print("密码至少8位"); return

    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    users = []
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH) as f:
            users = json.load(f)

    # 更新或创建 admin
    for u in users:
        if u["username"] == "admin":
            u["password_hash"] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            u["role"] = "admin"
            break
    else:
        users.append({
            "username": "admin",
            "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            "role": "admin",
            "created_at": datetime.now().isoformat(),
        })

    with open(USERS_PATH, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    print(f"admin 账户已创建/更新，密码: {password}")

if __name__ == "__main__":
    main()
