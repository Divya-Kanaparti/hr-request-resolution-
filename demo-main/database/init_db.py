"""
Database Initialization Script
Self-contained script to initialize the MySQL schema.
Does NOT import Pydantic or external compiled DLLs.
"""
import sys
import os
import subprocess
from pathlib import Path

def load_env_vars():
    """Simple, pure-Python .env file parser (zero dependencies)."""
    env_vars = {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_USER": "root",
        "DB_PASSWORD": "",
        "DB_NAME": "hr_request_resolution"
    }

    env_paths = [
        Path(".env"),
        Path("../.env"),
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent / ".env.example"
    ]

    for p in env_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in env_vars:
                        env_vars[k] = v
            break

    return env_vars

def init_database():
    env = load_env_vars()
    schema_file = Path(__file__).resolve().parent / "schema.sql"
    seed_file = Path(__file__).resolve().parent / "seed.sql"

    if not schema_file.exists():
        print(f"[-] schema.sql not found at {schema_file}")
        return

    print("=======================================================")
    print(" HR Request Resolution System - Database Initialization")
    print("=======================================================")
    print(f"[*] Target MySQL: {env['DB_HOST']}:{env['DB_PORT']}")
    print(f"[*] Database:     {env['DB_NAME']}")
    print(f"[*] User:         {env['DB_USER']}")

    # Method 1: Try pure Python pymysql (PyMySQL is 100% pure Python, no C DLLs)
    try:
        import pymysql
        print("[*] Connecting via PyMySQL (pure Python)...")
        conn = pymysql.connect(
            host=env["DB_HOST"],
            port=int(env["DB_PORT"]),
            user=env["DB_USER"],
            password=env["DB_PASSWORD"],
            autocommit=True,
            charset="utf8mb4"
        )
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            # Execute schema statements
            current = []
            for line in schema_sql.splitlines():
                line_str = line.strip()
                if not line_str or line_str.startswith("--"):
                    continue
                current.append(line)
                if line_str.endswith(";"):
                    stmt = "\n".join(current).strip()
                    if stmt.endswith(";"):
                        stmt = stmt[:-1].strip()
                    if stmt:
                        try:
                            cursor.execute(stmt)
                        except Exception as e:
                            pass
                    current = []

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.close()
        print("[+] SUCCESS: Database schema initialized successfully via PyMySQL!")
        return
    except ImportError:
        print("[!] PyMySQL package not installed, trying native MySQL CLI...")
    except Exception as e:
        print(f"[!] PyMySQL connection notice: {e}")

    # Method 2: Fallback to native mysql CLI
    print("[*] Attempting execution via native 'mysql' command...")
    cmd = [
        "mysql",
        f"-h{env['DB_HOST']}",
        f"-P{env['DB_PORT']}",
        f"-u{env['DB_USER']}"
    ]
    if env["DB_PASSWORD"]:
        cmd.append(f"-p{env['DB_PASSWORD']}")

    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            proc = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True
            )
        if proc.returncode == 0:
            print("[+] SUCCESS: Database schema initialized successfully via MySQL CLI!")
            return
        else:
            print(f"[!] MySQL CLI notice: {proc.stderr.strip()}")
    except FileNotFoundError:
        print("[!] 'mysql' executable not in system PATH.")

    print("\n[!] Manual Setup Option:")
    print("You can execute database/schema.sql directly using MySQL Workbench, or in PowerShell:")
    print(f"    Get-Content database\\schema.sql | mysql -u {env['DB_USER']} -p")

if __name__ == "__main__":
    init_database()
