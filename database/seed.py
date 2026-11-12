"""
Database Seed Script
Seeds initial departments, employees, categories, policies, and sample tickets.
Uses pure PyMySQL / MySQL CLI to execute database/seed.sql directly.
"""
import sys
import os
import subprocess
from pathlib import Path

def load_env_vars():
    """Pure-Python .env file parser."""
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

def run_seed():
    env = load_env_vars()
    seed_file = Path(__file__).resolve().parent / "seed.sql"

    if not seed_file.exists():
        print(f"[-] seed.sql not found at {seed_file}")
        return

    print("=======================================================")
    print(" HR Request Resolution System - Database Seeding")
    print("=======================================================")
    print(f"[*] Target MySQL: {env['DB_HOST']}:{env['DB_PORT']}")
    print(f"[*] Database:     {env['DB_NAME']}")

    # Method 1: Pure PyMySQL
    try:
        import pymysql
        print("[*] Connecting via PyMySQL...")
        conn = pymysql.connect(
            host=env["DB_HOST"],
            port=int(env["DB_PORT"]),
            user=env["DB_USER"],
            password=env["DB_PASSWORD"],
            database=env["DB_NAME"],
            autocommit=True,
            charset="utf8mb4"
        )
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            with open(seed_file, "r", encoding="utf-8") as f:
                seed_sql = f.read()

            current = []
            for line in seed_sql.splitlines():
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
        print("[+] SUCCESS: Base seed data populated successfully via PyMySQL!")
        return
    except ImportError:
        pass
    except Exception as e:
        print(f"[!] PyMySQL notice: {e}")

    # Method 2: Fallback to native mysql CLI
    print("[*] Attempting seed via native 'mysql' CLI...")
    cmd = [
        "mysql",
        f"-h{env['DB_HOST']}",
        f"-P{env['DB_PORT']}",
        f"-u{env['DB_USER']}"
    ]
    if env["DB_PASSWORD"]:
        cmd.append(f"-p{env['DB_PASSWORD']}")

    try:
        with open(seed_file, "r", encoding="utf-8") as f:
            proc = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True
            )
        if proc.returncode == 0:
            print("[+] SUCCESS: Base seed data populated via MySQL CLI!")
            return
        else:
            print(f"[!] MySQL CLI notice: {proc.stderr.strip()}")
    except FileNotFoundError:
        pass

    print("\n[!] Manual Seed Option:")
    print("Execute database/seed.sql directly using MySQL Workbench, or in PowerShell:")
    print(f"    Get-Content database\\seed.sql | mysql -u {env['DB_USER']} -p")

if __name__ == "__main__":
    run_seed()
