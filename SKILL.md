# Chore Chart Skill

> This file is read by the AI agent (OpenClaw or Claude Code) to understand what
> this skill does and how to invoke it. If you are an AI agent reading this: use
> `dispatch.py` with the subcommands below. Read `chore_schema.json` for the
> family configuration. Do not modify the schema unless the user asks you to.

Reads `chore_schema.json` and sends family chore assignments via Telegram (or any
configured channel). Designed to run on a cron schedule — one weekly reminder on
Sunday evening, plus an on-demand status command.

---

## Subcommands

```
python dispatch.py remind          # Weekly message: who has which group this week
python dispatch.py today           # Today's chores for every kid (based on day of week)
python dispatch.py today --kid Alex        # Today's chores for one kid
python dispatch.py today --group A         # Today's chores for one group
python dispatch.py status          # Full rotation table as text (debug / manual check)
python dispatch.py remind --dry-run        # Print without sending
```

---

## Setup

**1. Point to your schema:**

```bash
export CHORE_SCHEMA_FILE=/path/to/chore_schema.json
```

Default: `chore_schema.json` in the same directory as `dispatch.py`.

**2. Configure the send command:**

```bash
export CHORE_SEND_CMD="python /path/to/send-telegram.py"
```

The command receives the message text on stdin. Any command that reads stdin and
delivers it works — Telegram bot, email, Slack, `cat` for testing.

If `CHORE_SEND_CMD` is not set, the message is printed to stdout.

**3. Set your Sunday cron (4pm PT = 00:00 UTC Monday):**

```
0 16 * * SUN python /path/to/dispatch.py remind
```

---

## Environment variables

| Variable           | Default                          | Description                          |
|--------------------|----------------------------------|--------------------------------------|
| `CHORE_SCHEMA_FILE`| `chore_schema.json` (same dir)   | Path to your family's schema         |
| `CHORE_SEND_CMD`   | _(print to stdout)_              | Shell command to deliver the message |
| `CHORE_LOG_FILE`   | `dispatch.log` (same dir)        | Log file path                        |
| `CHORE_DRY_RUN`    | `0`                              | Set to `1` to print without sending  |

---

## Schema compatibility

Reads the same `chore_schema.json` produced by the web tool (`index.html`).
Required fields: `kids`, `num_groups`, `weeks_per_assignment`, `reference_monday`,
`chores`, `groups`, `group_totals_minutes_per_week`.
