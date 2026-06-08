Stakeholder Demo — Where & How to Show the ML
The demo is tomorrow, audience is non-technical execs/funders, and you want a simulator-driven live scenario. The web app already has a dashboard layout that exposes the ML outputs in the right places — you don't need to build anything new. Here's the playbook.

1. What to call the ML (for the audience)
Don't say "model," "features," "inference." Use one consistent phrase:

"The system's risk score — it's continuously reading the sensors and telling us which slopes are at risk."

Every time ML outputs appear on screen, refer back to "the risk score."

2. The three "money shots" on the dashboard
These are the screens that show ML outputs, in the order I'd walk through them.

A. Top KPIs — dashboard/page.tsx:53-78
Four cards across the top. Two of these are ML-driven:

Active Alerts (red) — count of nodes the model is currently flagging
24h Rainfall (sky) — the dominant input feature
Talking point: "These four numbers summarize the whole region in one glance — alerts, online sensors, rainfall, and battery health."

B. Map + Alert list — dashboard/page.tsx:81-117
This is the headline view. The severity dots on the map and the alerts panel are direct model outputs. Click a node and the alert detail shows why the model flagged it.

Talking point: "Each colored dot is a sensor location. The color is the system's current risk assessment — green is normal, yellow is watch, orange is warning, red is critical. Every red dot represents a slope the model believes needs attention."

C. Node grid (the sparklines) — dashboard/page.tsx:120-175
Every node card has a small rainfall sparkline with color tied to severity. This is the most "alive" part of the dashboard during a live scenario — you can see the dots turn color as the simulator drives the model.

Talking point: "These little charts are the last 24 hours of rainfall per sensor. Watch what happens to the color when I trigger a heavy-rain event in the simulator."

3. The live scenario script (5–7 minutes)
The simulator at services/simulator/app.py is the trigger. Before the meeting, have a terminal ready with the simulator command.

Step 1 — Cold start (2 min)

Open /dashboard. Point at the map: "Right now everything is calm. The model is reading every node every 15 minutes, and it's assessed all slopes as normal."
Hover over one node, click it. Show the alert detail with confidence/severity fields. "This is what a model output looks like under the hood — it tells us not just the level, but how confident it is."
Step 2 — Trigger a scenario (1 min)

In the terminal, run a heavy-rain injection via the simulator (e.g., spike a node's rain). The dashboard should re-render with new sparkline data within ~15s (the polling interval).
"I'm now simulating 3 hours of heavy rain on the north ridge in 30 seconds."
Step 3 — Watch the model react (1–2 min)

The rainfall KPI climbs. One of the sparklines spikes. The node's severity dot transitions Normal → Watch → Warning → Critical.
A new alert appears in the right panel.
"Notice the system didn't just say 'rain fell' — it raised the alert because the rainfall pattern crossed the model's threshold for this terrain type. That's the difference between a sensor and a decision-support system."
Step 4 — Show the drill-down (1 min)

Click the critical node. Open the alert. Show the contributing factors / model explanation if present, or the reading history.
"This is the level of detail an operator gets. For stakeholders, the takeaway is: every alert comes with evidence the team can verify."
Step 5 — Land the message (30s)

Close the dashboard. "What you saw was the model taking raw sensor noise — rainfall, tilt, vibration, battery — and turning it into a single, actionable risk score per slope, updated every 15 minutes, across 5 sites. That decision support is what scales across a region in a way that human monitoring alone cannot."
4. Pre-flight checklist (do this tonight)
The fixtures vs. live data issue. Right now the dashboard imports from @/lib/fixtures — see dashboard/page.tsx:6-14. Confirm whether the dashboard is wired to live API or to static fixtures. If fixtures, the simulator injection won't visibly change the dashboard — you'd need to either (a) switch the dashboard to live data, or (b) drive the demo against a pre-seeded scenario. This is the #1 thing to verify before tomorrow.
Start the stack: pnpm dev (or whichever the Makefile defines — see landslide-ews/Makefile). Confirm the dashboard renders without errors.
Run the simulator once end-to-end so you know the command and the latency.
Open the demo in the actual browser you'll present on. Resize to the projector resolution. Check font sizes — text-3xl for KPIs is fine, but body text (text-xs/text-sm) is small for a room.
Have a fallback: a screenshot of the dashboard already showing a critical alert, in case live data flakes.
5. The one thing I'd verify right now
The single biggest risk for tomorrow is whether the dashboard page reads live data or fixtures. Quick check you can do:

Open apps/web/app/(app)/dashboard/page.tsx — line 14 imports KPI, NODES, NODE_SEVERITIES, ALERTS from @/lib/fixtures. That's static data.
Check apps/web/lib/fixtures.ts to see if it has any logic that pulls from the API, or if it's purely hand-written constants.
