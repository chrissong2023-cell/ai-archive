# Durable & Background Systems

Four systems run alongside the main conversation loop. Quick reference
here; full developer notes live in `AGENTS.md`, user-facing docs under
`website/docs/user-guide/features/`.

### Delegation (`delegate_task`)

Spawn a subagent with an isolated context + terminal session.

- **Single:** `delegate_task(goal, context)`.
- **Batch:** `delegate_task(tasks=[{goal, ...}, ...])` runs children in
  parallel, capped by `delegation.max_concurrent_children` (default 3).
- **Background:** `delegate_task(background=true)` returns a handle
  immediately and keeps the parent loop going; the child's result
  re-enters the conversation as a new turn when it finishes.
- **Roles:** `leaf` (default; cannot re-delegate) vs `orchestrator`
  (can spawn its own workers, bounded by `delegation.max_spawn_depth`).
- **Not durable.** A backgrounded child is still process-local — if the
  parent process exits, the child is lost. For work that must outlive
  the process, use `cronjob` or
  `terminal(background=True, notify_on_complete=True)`.

Config: `delegation.*` in `config.yaml`.

### Cron (scheduled jobs)

Durable scheduler — `cron/jobs.py` + `cron/scheduler.py`. Drive it via
the `cronjob` tool, the `hermes cron` CLI (`list`, `add`, `edit`,
`pause`, `resume`, `run`, `remove`), or the `/cron` slash command.

- **Schedules:** duration (`"30m"`, `"2h"`), "every" phrase
  (`"every monday 9am"`), 5-field cron (`"0 9 * * *"`), or ISO timestamp.
- **Per-job knobs:** `skills`, `model`/`provider` override, `script`
  (pre-run data collection; `no_agent=True` makes the script the whole
  job), `context_from` (chain job A's output into job B), `workdir`
  (run in a specific dir with its `AGENTS.md` / `CLAUDE.md` loaded),
  multi-platform delivery.
- **Making a job that actually runs:** when the prompt says "load skill
  X", also pass `skills=["x"]` — the job runs in a fresh session with no
  chat context, and the explicit attach is what guarantees the procedure
  is loaded. Spell `enabled_toolsets` with **registered toolset names**
  (`file` — singular — plus `web`, `terminal`): a wrong name silently
  narrows the job's tools, so a job that needs to write files can end up
  with no file tool and no error at creation time.
- **Verify by firing, not by creating:** existence of the job proves
  nothing. `action='run'` fires it once in the background (outcome
  re-enters the conversation later — do not poll), and the run's full
  transcript lands at `~/.hermes/cron/output/<job_id>/<timestamp>.md`
  with the injected script stdout and the final response. Read that file
  to confirm the script ran, the skill loaded, and files were written.
- **Delivery is a separate failure mode from running — check
  `last_status` / `last_delivery_error` in `action='list'`.** A job can
  run green every tick for days and deliver nothing. `deliver='origin'`
  means "the chat this job was created from"; a job created
  programmatically (tool call, script, CLI) has **no** chat origin, so
  it falls back to the platform home channel — if that channel is
  unpaired or its session has expired, every delivery fails while the
  run itself stays fine. Before reporting a recurring job as working,
  confirm where its output actually goes; if no target can be verified
  as reachable, set `deliver='local'` so output stops erroring and stays
  readable under `~/.hermes/cron/output/<job_id>/`, and surface it in
  conversation until a working channel exists.
- **Delivery targets are resolved, not guessed.** `deliver='wecom'` (or
  any bare platform name) fails with `no delivery target resolved`; the
  grammar is `platform:chat_id[:thread_id]`. A platform *username* is not
  a chat id — WeCom answers `errcode 93006 invalid chatid`. Some adapters
  also refuse to push until the human has messaged the bot at least once
  (`iLink … session not ready: the user must send the bot a message
  first (or re-pair)`); that is fixed by one inbound message, not by
  retrying or editing the job. Report the resolved target explicitly and
  say plainly when nothing reached the user.
- **`no_agent=True` suppresses on EMPTY stdout.** `[SILENT]` is the
  agent-mode token; a script job that prints it delivers the literal
  string. Keep a script job quiet by printing nothing at all.
- **Never pass `enabled_toolsets: []`.** An empty list is an explicit
  zero-tool allowlist, and with no callable tools the model can emit
  tool-call markup as prose (XML-ish `<|…|>` blocks) that then gets
  delivered as the answer. Give the job the smallest *real* toolset it
  needs.
- **`script` output is context, not delivery:** stdout is injected into
  the prompt as pre-fetched data (scripts resolve under
  `~/.hermes/scripts/`), while only the agent's final response is what
  gets delivered to the target.
- **Invariants:** 3-minute hard interrupt per run, `.tick.lock` file
  prevents duplicate ticks across processes, cron sessions pass
  `skip_memory=True` by default, and cron deliveries are framed with a
  header/footer instead of being mirrored into the target gateway
  session (keeps role alternation intact).

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron

### Curator (skill lifecycle)

Background maintenance for agent-created skills. Tracks usage, marks
idle skills stale, archives stale ones, keeps a pre-run tar.gz backup
so nothing is lost.

- **CLI:** `hermes curator <verb>` — `status`, `usage`, `run`, `pause`,
  `resume`, `pin`, `unpin`, `archive`, `restore`, `list-archived`, `prune`,
  `backup`, `rollback`.
- **Slash:** `/curator <subcommand>` mirrors the CLI.
- **Scope:** only touches skills with `created_by: "agent"` provenance.
  Bundled + hub-installed skills are off-limits. **Never deletes** —
  max destructive action is archive. Pinned skills are exempt from
  every auto-transition and every LLM review pass.
- **Cost:** the deterministic inactivity/prune sweep runs for free. The
  aux-model "consolidate overlapping skills into umbrellas" pass is
  **off by default** — opt in with `curator.consolidate: true` or
  `hermes curator run --consolidate`. Routine background curation costs
  zero tokens.
- **Telemetry:** sidecar at `~/.hermes/skills/.usage.json` holds
  per-skill `use_count`, `view_count`, `patch_count`,
  `last_activity_at`, `state`, `pinned`.

Config: `curator.*` (`enabled`, `interval_hours`, `min_idle_hours`,
`stale_after_days`, `archive_after_days`, `backup.*`).
User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator

### Kanban (multi-agent work queue)

Durable SQLite board for multi-profile / multi-worker collaboration.
Users drive it via `hermes kanban <verb>`; dispatcher-spawned workers
see a focused `kanban_*` toolset gated by `HERMES_KANBAN_TASK`, and
orchestrator profiles can opt into the broader `kanban` toolset. Normal
sessions still have zero `kanban_*` schema footprint unless configured.

- **CLI verbs (common):** `init`, `create`, `list` (alias `ls`),
  `show`, `assign`, `link`, `unlink`, `comment`, `complete`, `block`,
  `unblock`, `archive`, `tail`. Less common: `watch`, `stats`, `runs`,
  `log`, `dispatch`, `daemon`, `gc`.
- **Worker/orchestrator toolset:** `kanban_show`, `kanban_complete`,
  `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`,
  `kanban_link`; profiles that explicitly enable the `kanban` toolset
  outside a dispatcher-spawned task also get `kanban_list` and
  `kanban_unblock` for board routing.
- **Dispatcher** runs inside the gateway by default
  (`kanban.dispatch_in_gateway: true`) — reclaims stale claims,
  promotes ready tasks, atomically claims, spawns assigned profiles.
  Auto-blocks a task after `failure_limit` consecutive spawn failures
  (default 2; configurable via `kanban.failure_limit` or per-task
  `max_retries`).
- **Isolation:** board is the hard boundary (workers get
  `HERMES_KANBAN_BOARD` pinned in env); tenant is a soft namespace
  within a board for workspace-path + memory-key isolation.

User docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
