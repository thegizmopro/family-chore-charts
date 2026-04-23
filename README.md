# Family Chore Charts

A configurable chore chart system for families with rotating assignments. Built for households with multiple kids where fairness matters.

## What it does

- Enter your family's chores, kids, and schedule
- Auto-balances chores into groups by weekly time
- Shows a fairness visualization — proves every kid does equal work over the rotation
- Generates printable weekly charts with day-by-day checkboxes
- Shareable URL encodes your family's config — text it to another parent and they get your exact setup

## Use it

**[Open the app →](https://thegizmopro.github.io/family-chore-charts)**

No login. No account. Works offline once loaded.

## How the rotation works

Kids rotate through chore groups on a fixed cycle. With 3 kids and 1 week per assignment:

| Week | Kid 1 | Kid 2 | Kid 3 |
|------|-------|-------|-------|
| 1    | Group A | Group B | Group C |
| 2    | Group B | Group C | Group A |
| 3    | Group C | Group A | Group B |
| 4    | repeats... | | |

Every kid does every group equally. The fairness graph shows the running balance.

## OpenClaw skill

If you use [OpenClaw](https://openclaw.dev), `dispatch.py` is a skill that sends weekly reminders and daily chore lists via Telegram (or any delivery channel).

```bash
python dispatch.py remind          # Sunday reminder: who has which group
python dispatch.py today           # Today's chores for each kid
python dispatch.py today --kid Alex
python dispatch.py status          # Full rotation table
```

See `SKILL.md` for setup.

## Files

| File | Purpose |
|------|---------|
| `index.html` | The web app — self-contained, no dependencies |
| `balancer.js` | Chore balancing algorithm (greedy bin-packing) |
| `chore_schema.json` | Seed data — replace with your family's chores |
| `dispatch.py` | OpenClaw skill for Telegram reminders |
| `SKILL.md` | Skill setup and usage |
| `balancer.test.js` | Tests — run with `node balancer.test.js` |

## Your own family

1. Open the app and click **Load Example** to see the seed data
2. Edit names, chores, schedule to match your household
3. Click **Generate Charts**, then **Export JSON** to save your config
4. Use **Share URL** to send your config to another family

## License

MIT
