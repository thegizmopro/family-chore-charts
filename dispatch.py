#!/usr/bin/env python3
"""
dispatch.py — Chore chart dispatch engine (Python 3.9+, stdlib only)

Subcommands:
    remind              Weekly message: who has which group this week
    today               Today's chores for every kid
    today --kid NAME    Today's chores for one kid
    today --group A     Today's chores for one group
    status              Full rotation table (text)

Flags:
    --dry-run           Print without sending

Environment:
    CHORE_SCHEMA_FILE   Path to chore_schema.json  (default: same dir as script)
    CHORE_SEND_CMD      Shell command that reads message text on stdin
    CHORE_LOG_FILE      Log file path              (default: same dir as script)
    CHORE_DRY_RUN       Set to 1 to force dry-run
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

if sys.version_info < (3, 9):
    sys.exit(f"Python 3.9+ required — found {sys.version.split()[0]}")

# Force UTF-8 on Windows consoles that default to cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent.resolve()
SCHEMA_FILE = Path(os.environ.get("CHORE_SCHEMA_FILE", SCRIPT_DIR / "chore_schema.json"))
LOG_FILE    = Path(os.environ.get("CHORE_LOG_FILE",    SCRIPT_DIR / "dispatch.log"))
SEND_CMD    = os.environ.get("CHORE_SEND_CMD", "")
DRY_RUN_ENV = os.environ.get("CHORE_DRY_RUN", "0") == "1"

GROUP_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DAY_NAMES    = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]  # 0=Monday

log = logging.getLogger("chore-dispatch")

# ── Logging ───────────────────────────────────────────────────────────────────

def setup_logging(dry_run: bool) -> None:
    level = logging.DEBUG if dry_run else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )

# ── Schema ────────────────────────────────────────────────────────────────────

def load_schema() -> dict:
    if not SCHEMA_FILE.exists():
        sys.exit(f"Schema not found: {SCHEMA_FILE}\n"
                 f"Set CHORE_SCHEMA_FILE or put chore_schema.json next to dispatch.py.")
    with SCHEMA_FILE.open(encoding="utf-8") as f:
        schema = json.load(f)
    required = ["kids", "num_groups", "reference_monday", "chores", "groups",
                "group_totals_minutes_per_week"]
    missing = [k for k in required if k not in schema]
    if missing:
        sys.exit(f"Schema missing fields: {', '.join(missing)}")
    return schema

# ── Rotation logic ────────────────────────────────────────────────────────────

def weeks_since_reference(schema: dict) -> int:
    """Signed number of weeks between this Monday and the reference Monday."""
    ref = date.fromisoformat(schema["reference_monday"])
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())  # 0=Monday
    return (this_monday - ref).days // 7

def current_rotation(schema: dict) -> int:
    """0-indexed rotation step (0 = first week of cycle)."""
    wpa   = schema.get("weeks_per_assignment", 1)
    n     = schema["num_groups"]
    total = n * wpa
    pos   = weeks_since_reference(schema) % total
    if pos < 0:
        pos += total
    return pos // wpa

def assignments(schema: dict) -> dict[str, str]:
    """Return {kid_name: group_label} for the current rotation."""
    labels = list(GROUP_LABELS[:schema["num_groups"]])
    rot    = current_rotation(schema)
    return {
        kid: labels[(i + rot) % schema["num_groups"]]
        for i, kid in enumerate(schema["kids"])
    }

def chores_for_group(schema: dict, group: str) -> list[dict]:
    """Return chore objects for a group label, in assignment order."""
    ids = schema["groups"].get(group, [])
    by_id = {c["id"]: c for c in schema["chores"]}
    return [by_id[i] for i in ids if i in by_id]

def chores_for_today(schema: dict, group: str) -> list[dict]:
    """Chores in group that are scheduled for today (or are as-needed)."""
    today_day = DAY_NAMES[date.today().weekday()]
    result = []
    for c in chores_for_group(schema, group):
        if c.get("as_needed"):
            result.append(c)
        elif today_day in c.get("days", []):
            result.append(c)
    return result

# ── Formatters ────────────────────────────────────────────────────────────────

def fmt_remind(schema: dict) -> str:
    assign   = assignments(schema)
    totals   = schema["group_totals_minutes_per_week"]
    family   = schema.get("family", "Family")
    wpa      = schema.get("weeks_per_assignment", 1)

    # Date range: find the Monday that started this assignment step
    offset      = weeks_since_reference(schema)
    this_monday = date.today() - timedelta(days=date.today().weekday())
    assign_start = this_monday - timedelta(weeks=(offset % wpa))
    assign_end   = assign_start + timedelta(weeks=wpa, days=-1)

    if wpa == 1:
        date_line = f"Week of {assign_start.strftime('%b %d')}"
    else:
        date_line = f"{assign_start.strftime('%b %d')} – {assign_end.strftime('%b %d')}"

    lines = [f"🧹 {family} chores — {date_line}!", ""]
    for kid, group in assign.items():
        mins = totals.get(group, "?")
        lines.append(f"  {kid} → Group {group}  (~{mins} min/wk)")
    return "\n".join(lines)

def fmt_today(schema: dict, kid: Optional[str] = None, group: Optional[str] = None) -> str:
    assign = assignments(schema)
    today  = date.today()
    today_label = today.strftime("%A, %b %d")

    # Resolve target(s)
    if kid:
        if kid not in assign:
            return f"Kid '{kid}' not found. Kids: {', '.join(assign.keys())}"
        targets = [(kid, assign[kid])]
    elif group:
        group = group.upper()
        kids_in_group = [k for k, g in assign.items() if g == group]
        if not kids_in_group:
            return f"Group '{group}' not found or has no kids assigned this week."
        targets = [(k, group) for k in kids_in_group]
    else:
        targets = list(assign.items())

    sections = []
    for k, g in targets:
        chores = chores_for_today(schema, g)
        header = f"📋 {k} — Group {g} — {today_label}"
        if not chores:
            sections.append(f"{header}\n  (No chores scheduled today)")
            continue
        items = []
        for c in chores:
            suffix = " (as needed)" if c.get("as_needed") else f" ({c['minutes']} min)"
            items.append(f"  • {c['name']}{suffix}")
        sections.append(header + "\n" + "\n".join(items))

    return "\n\n".join(sections)

def fmt_status(schema: dict) -> str:
    labels  = list(GROUP_LABELS[:schema["num_groups"]])
    wpa     = schema.get("weeks_per_assignment", 1)
    rot     = current_rotation(schema)
    kids    = schema["kids"]
    totals  = schema["group_totals_minutes_per_week"]

    header_kids = "  ".join(f"{k:<12}" for k in kids)
    lines = [
        f"Rotation status — {schema.get('family', 'Family')}",
        f"{'Step':<12}  {header_kids}",
        "-" * (14 + 14 * len(kids)),
    ]
    for step in range(schema["num_groups"]):
        start = step * wpa + 1
        end   = start + wpa - 1
        step_label = f"Wk {start}" if wpa == 1 else f"Wk {start}–{end}"
        marker = " <- NOW" if step == rot else ""
        kid_groups = "  ".join(
            f"{'Group ' + labels[(i + step) % schema['num_groups']]:<12}"
            for i in range(len(kids))
        )
        lines.append(f"{step_label + marker:<12}  {kid_groups}")

    lines += ["", "Group totals (min/wk):"]
    for label in labels:
        lines.append(f"  Group {label}: {totals.get(label, '?')} min")
    return "\n".join(lines)

# ── Send ──────────────────────────────────────────────────────────────────────

def send(message: str, dry_run: bool) -> None:
    log.info("Message:\n%s", message)
    if dry_run:
        print("--- DRY RUN -----------------------------------")
        print(message)
        print("----------------------------------------------")
        return
    if not SEND_CMD:
        print(message)
        return
    try:
        result = subprocess.run(
            SEND_CMD, shell=True, input=message,
            text=True, capture_output=True, timeout=30,
        )
        if result.returncode != 0:
            log.error("Send command failed (exit %d): %s", result.returncode, result.stderr.strip())
            sys.exit(1)
        log.info("Sent via: %s", SEND_CMD)
    except subprocess.TimeoutExpired:
        log.error("Send command timed out after 30s")
        sys.exit(1)

# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    # --dry-run is accepted before or after the subcommand
    dryrun_parent = argparse.ArgumentParser(add_help=False)
    dryrun_parent.add_argument("--dry-run", action="store_true")

    parser = argparse.ArgumentParser(description="Chore chart dispatch engine",
                                     parents=[dryrun_parent])
    sub    = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("remind", parents=[dryrun_parent], help="Weekly rotation reminder")
    sub.add_parser("status", parents=[dryrun_parent], help="Full rotation table")

    p_today = sub.add_parser("today", parents=[dryrun_parent], help="Today's chores")
    grp = p_today.add_mutually_exclusive_group()
    grp.add_argument("--kid",   metavar="NAME",  help="Filter to one kid")
    grp.add_argument("--group", metavar="LABEL", help="Filter to one group (A/B/C…)")

    args     = parser.parse_args()
    dry_run  = args.dry_run or DRY_RUN_ENV
    setup_logging(dry_run)

    schema = load_schema()

    if args.cmd == "remind":
        message = fmt_remind(schema)
    elif args.cmd == "today":
        message = fmt_today(schema, kid=getattr(args, "kid", None),
                            group=getattr(args, "group", None))
    elif args.cmd == "status":
        message = fmt_status(schema)
    else:
        parser.print_help()
        sys.exit(1)

    send(message, dry_run)

if __name__ == "__main__":
    main()
