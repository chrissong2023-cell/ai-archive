---
name: weekly-review-planning
description: "Weekly reset: commitments, stalled work, next-week plan."
version: 0.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Weekly-Review, Planning, Tasks, Calendar, Productivity]
    related_skills: [obsidian, notion, airtable, google-workspace, email-inbox-triage]
---

# Weekly Review and Planning

Run a bounded weekly reset across the user's chosen systems. This is a concrete recurring task, not a generic productivity methodology — the `weekly-review` Automation Blueprint schedules it as a cron job.

## When to Use

- "Run my weekly review."
- "What did I commit to and what is slipping?"
- "Plan next week from my calendar, tasks, and notes."
- "Find stale projects and waiting items."
- A cron tick fires for a scheduled weekly review.

Don't use for: daily briefs (see the `google-workspace` daily-brief reference) or single-inbox triage (`email-inbox-triage`).

## Procedure

### 1. Set systems and window

Confirm timezone, review period, planning horizon, authoritative task/project store, calendars, inboxes, and allowed writes. Default to recommendations/drafts, not mutations. Done when source-of-truth conflicts have a declared winner.

### 2. Review calendar evidence

Load `google-workspace` or the relevant calendar connector. Inspect the completed week for meetings and commitments, then the next 1-2 weeks for deadlines, travel, preparation, and capacity. Capture follow-ups implied by past events and conflicts ahead. Done when both retrospective and horizon are covered.

### 3. Clear capture inboxes

Review the task inbox, notes (`obsidian`, `notion`), flagged email (`email-inbox-triage` owns thread-level triage), and other declared capture points. Convert each item to next action, project, waiting, scheduled, someday, reference, archive, or delete proposal. Do not mutate until scope is approved. Done when remaining unprocessed items are counted and stated.

### 4. Reconcile active projects

For each project identify desired outcome, next action, owner, deadline, blocker, last meaningful activity, and source link. Flag projects with no next action, missed dates, duplicate records, or contradictory status. Done when every active project is actionable or explicitly paused.

### 5. Review waiting and commitments

Find promises made by the user and items owed by others. Propose follow-ups with dates and channels. Do not infer that silence means completion. Done when each waiting item has an owner and next review/follow-up date.

### 6. Build a capacity-aware plan

Estimate fixed calendar load and select a small set of weekly outcomes plus near-term next actions. Rank by consequence, deadline, dependency, and effort; do not fill every free hour. Done when the plan fits actual capacity and names deferred work.

### 7. Apply approved updates

Update tasks/projects, create calendar holds, archive processed items, and draft follow-ups only as approved. Read every changed record back from the provider. Done when verified writes match the review summary.

## Output Shape

1. Wins and completed commitments
2. Overdue or at risk
3. Waiting/follow-ups
4. Stalled or ambiguous projects
5. Next week's outcomes and calendar constraints
6. Proposed updates awaiting approval
7. Coverage gaps

## When the ask is "I feel scattered" — build a daily driver, not another plan

- **Check for an existing strategy first** (plan folder, project index, task ledger). If one exists, a second plan is the wrong deliverable: write the single page that drives a day and say plainly that the strategy already exists.
- **One page, two or three fixed windows with clock times** — what the user does in each, and what the agent has pre-staged before they arrive (decision list, drafted replies, money snapshot).
- **Exactly one approval window per day.** Everything needing sign-off queues there; only money, seal, legal/regulatory or a live client escalation may interrupt. Unbounded approvals are what makes a day feel fragmented.
- **State the split explicitly**: what the agent takes over by default (drafting, costing, research, filing, chasing) vs what only the user can do (pricing, signing, payment, compliance judgement, key relationships). A scattered user is usually the sole decision bottleneck — naming the boundary is the actual relief.
- **Cap the week at ~5 must-dos pulled from the existing ledger** (open items with a deadline or real risk first), and name which open items are explicitly *not* this week.
- Add the anti-queue rules that keep it working: the 2-minute rule (do it now or hand it over), "waiting until I have time" equals never, deep blocks with messaging off.
- **Metrics must be measured, not aspirational** — median first-reply latency, age of the oldest pending approval, number of dormant contacts, pipeline counts. Pull them from the ledger so next week's review can show real movement.

## Pitfalls

- Answering "I'm scattered" with a fresh roadmap when one already exists — it adds a document instead of removing a decision.
- Planning a day with no fixed approval window, so every incoming request interrupts the deep blocks.
- Planning from tasks without calendar capacity.
- Carrying every unfinished item forward as high priority.
- Marking projects active with no next action.
- Silently deleting or rescheduling personal commitments.
- Treating silence from others as completion.

## Verification

- [ ] Both the completed week and the planning horizon were covered, or gaps are stated.
- [ ] Every stalled/waiting flag traces to a specific record, event, or thread.
- [ ] No task, event, or note was mutated without approval; approved writes were read back.
- [ ] The plan names what was deferred, not just what was chosen.
