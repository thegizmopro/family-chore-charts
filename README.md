# Family Chore Charts

A configurable chore chart system for families with rotating assignments. No login, no server, no subscription.

**[Open the app →](https://thegizmopro.github.io/family-chore-charts)**

---

## Getting started with the web tool

**1. Open the app**

Go to https://thegizmopro.github.io/family-chore-charts — or download `index.html` and open it directly in any browser. It works offline.

**2. Load the example (optional)**

Click **Load Example** to see a pre-filled family (The Smiths, 15 chores, 3 kids). This shows you how everything fits together before you enter your own data.

**3. Set up your family**

Fill in:
- **Family Name** — appears on the printed charts
- **Weeks per assignment** — how long each kid keeps their group before rotating (1 week is typical; choose 2 or 4 if you want less frequent swaps)
- **Groups** — one group per kid (3 kids = 3 groups)
- **Reference Monday** — the Monday your first rotation started (used to calculate who has what group this week)
- **Kids** — add each child's name in rotation order

**4. Enter your chores**

For each chore:
- **Name** — what it's called on the printed chart
- **Min** — how many minutes it takes
- **×/wk** — how many times per week
- **Days** — which days of the week (Mon, Tue, Wed…). For chores with no fixed day — like emptying trash when it's full — check **As needed** below the day boxes instead. The chart will print one checkbox per expected weekly occurrence so kids can tick off each time they do it. The time still counts toward the group total.
- **Instructions** — optional detail that prints under the chore name

**5. Generate charts**

Click **Generate Charts →**. The app:
- Auto-balances chores into groups by total weekly minutes
- Shows a **fairness visualization** — a bar chart proving each group is roughly equal
- Shows the **rotation table** with the current week highlighted
- Generates a **printable chart for each group** with the assigned kid's name and day-by-day checkboxes

**6. Print**

Click **Print** (top right). Each group prints on its own page. Post them on the wall.

**7. Save and share your config**

- **Export JSON** — downloads your family's config as a `.json` file. Keep this. It's your source of truth.
- **Share URL** — copies a link with your entire config encoded in it. Paste it into a text or email to share with another family.

---

## How the rotation works

Kids rotate through chore groups on a fixed cycle. With 3 kids and 1 week per assignment:

| Week | Kid 1 | Kid 2 | Kid 3 |
|------|-------|-------|-------|
| 1 | Group A | Group B | Group C |
| 2 | Group B | Group C | Group A |
| 3 | Group C | Group A | Group B |
| 4 | repeats... | | |

Every kid does every group equally over the full cycle. The fairness visualization shows the weekly minute totals so kids (and parents) can see it's balanced.

---

## OpenClaw AI skill

If you use [OpenClaw](https://openclaw.dev), `dispatch.py` is an AI agent skill that automates the weekly reminder. The agent reads `SKILL.md` to understand what the skill does and how to run it.

```bash
python dispatch.py remind          # Weekly message: who has which group
python dispatch.py today           # Today's chores for every kid
python dispatch.py today --kid Alex
python dispatch.py today --group A
python dispatch.py status          # Full rotation table
```

Point it at your exported `chore_schema.json`, set a `CHORE_SEND_CMD` to your Telegram bot or other delivery method, and add a Sunday cron. See `SKILL.md` for the full setup.

---

## Files

| File | Purpose |
|------|---------|
| `index.html` | The web app — self-contained, no build step, no dependencies |
| `balancer.js` | Chore balancing algorithm (shared by web tool and skill) |
| `chore_schema.json` | Example family config — replace with your own via Export JSON |
| `dispatch.py` | OpenClaw AI skill for automated reminders |
| `SKILL.md` | Instructions the AI agent reads to understand and run the skill |
| `balancer.test.js` | Algorithm tests — `node balancer.test.js` |

---

## License

MIT
