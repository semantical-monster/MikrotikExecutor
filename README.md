# tikExec

> Bulk command executor for MikroTik RouterOS devices — push configuration changes across an entire device fleet in one run.

---

## The Problem

When you manage a large number of MikroTik routers — CPEs, edge routers, headend gear — applying the same configuration change to each device manually over SSH doesn't scale. Whether it's a security hardening pass, a service access restriction, or a policy enforcement push, you want it done consistently across every device, with a log of what happened on each one.

## What It Does

`tikExec.py` reads a list of device IPs from `ipList.txt`, SSH's into each one using Paramiko, executes every command in the `COMMANDS` list sequentially, and writes the per-device output to `results.txt`.

The `COMMANDS` list is the only thing you need to change between jobs — add, remove, or swap commands freely. The loop handles everything else.

---

## Default Commands (Security Hardening Example)

The script ships with a MikroTik security hardening example out of the box:

| Command | What It Does |
|---------|-------------|
| `ip dns set allow-remote-requests=no` | Disables the open DNS resolver — prevents the device from being used as a DNS amplification vector |
| `ip service set winbox address=10.0.0.0/8` | Restricts Winbox management access to RFC1918 addresses only |
| `ip service set www address=10.0.0.0/8` | Restricts HTTP management to RFC1918 addresses only |
| `ip service set ssh address=10.0.0.0/8` | Restricts SSH access to RFC1918 addresses only |

Swap these out for whatever commands fit your job.

---

## Requirements

- Python 3.x
- [Paramiko](https://www.paramiko.org/)
- MikroTik devices with SSH enabled and reachable management IPs

```
pip install -r requirements.txt
```

---

## Setup

**1. Populate `ipList.txt`** with target device management IPs — one per line:

```
10.0.1.1
10.0.1.2
10.0.1.3
```

**2. Set your credentials and port** in `tikExec.py`:

```python
USERNAME = "admin"
PASSWORD = "your_password_here"
SSH_PORT = 2282   # adjust to match your environment
```

> ⚠️ Shared credentials across a managed device fleet is common in SP/WISP environments. Do not commit credentials to version control.

**3. Define your commands:**

```python
COMMANDS = [
    "ip dns set allow-remote-requests=no",
    "ip service set winbox address=10.0.0.0/8",
    # add or remove lines freely
]
```

**4. Run it:**

```bash
python tikExec.py
```

---

## Output

Console gives you live pass/fail feedback per device:

```
[OK]  10.0.1.1
[OK]  10.0.1.2
[FAIL] 10.0.1.3
...traceback...
```

`results.txt` logs per-device command output:

```
=== Results for 10.0.1.1 ===
  [ip dns set allow-remote-requests=no]
  (no output)
  [ip service set winbox address=10.0.0.0/8]
  (no output)
...

=== Results for 10.0.1.2 ===
...
```

MikroTik RouterOS typically returns no output on successful configuration commands — `(no output)` in the log means it worked.

---

## Notes

- Failed devices print a full traceback to console and are skipped — the rest of the run continues uninterrupted
- `results.txt` is opened in append mode — clear it between runs to avoid stale data
- SSH port defaults to `2282` — a common non-standard port used in MikroTik deployments to reduce exposure; adjust as needed

---

## Stack

`Python` · `Paramiko` · `MikroTik RouterOS` · `Network Automation`
