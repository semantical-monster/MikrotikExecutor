"""
tikExec.py
----------
Bulk command executor for MikroTik RouterOS devices.

Use Case:
    When you need to push configuration changes across a fleet of MikroTik
    devices simultaneously — security hardening, service lockdowns, policy
    enforcement, etc. — this script SSH's into each device in ipList.txt,
    executes all defined commands sequentially, and logs the output.

    The commands list is the only thing you need to modify between jobs.
    Add, remove, or swap commands freely — the loop handles the rest.

Usage:
    1. Add target device IPs (one per line) to ipList.txt
    2. Set credentials and SSH port below
    3. Define your commands in the COMMANDS list
    4. Run:  python tikExec.py
    5. Review results.txt for per-device output

Dependencies:
    paramiko

Author: semantical-monster
"""

import paramiko
import traceback

# ── Configuration ─────────────────────────────────────────────────────────────

IP_LIST_FILE = "ipList.txt"
OUTPUT_FILE  = "results.txt"
USERNAME     = "admin"
PASSWORD     = "password"       # <-- set before running
SSH_PORT     = 2282             # MikroTik default alt port; change if needed

# ── Commands to execute on every device ───────────────────────────────────────
# Add, remove, or swap commands here freely — no other code changes needed.

COMMANDS = [
    "ip dns set allow-remote-requests=no",      # Disable open DNS resolver
    "ip service set winbox address=10.0.0.0/8", # Restrict Winbox to RFC1918
    "ip service set www address=10.0.0.0/8",    # Restrict HTTP mgmt to RFC1918
    "ip service set ssh address=10.0.0.0/8",    # Restrict SSH to RFC1918
]

# ── Load target hosts ─────────────────────────────────────────────────────────

with open(IP_LIST_FILE, "r") as f:
    hosts = f.read().split()

# ── Execute against each device ───────────────────────────────────────────────

for host in hosts:
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            host,
            username=USERNAME,
            password=PASSWORD,
            port=SSH_PORT,
            look_for_keys=False
        )

        with open(OUTPUT_FILE, "a") as out:
            out.write(f"=== Results for {host} ===\n")

            for command in COMMANDS:
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode("utf-8")
                stdin.close()
                out.write(f"  [{command}]\n")
                out.write(f"  {output}\n" if output.strip() else "  (no output)\n")

            out.write("\n")

        client.close()
        print(f"[OK]  {host}")

    except Exception as exc:
        print(f"\n[FAIL] {host}:")
        print(traceback.format_exc())
        print(exc)
        print()
