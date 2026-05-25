# Mechanism PRD — Process Orchestrator

**Component:** `ProcessDebateOrchestrator`  
**Module:** `debate.orchestrator` (split in Stage 3)  
**Version:** 1.00  
**Authors:** Renat Karimov, Alon Engel  
**Last updated:** 2026-05-21

---

## 1. Summary

The process orchestrator is the **central runtime** for Exercise 02. It spawns and supervises three OS-level worker processes (Parent, Pro, Con), drives the ping loop, validates agent messages, writes the verdict, and emits progress events for CLI/GUI consumers.

---

## 2. Responsibilities

| Responsibility | Owner |
|----------------|-------|
| Load config and create session ID | Supervisor (main process) |
| Spawn Parent, Pro, Con workers with `spawn` context | Supervisor |
| Run ping loop (1..N per side) | Parent worker |
| Route messages (no Pro↔Con direct path) | Parent worker |
| Invoke LLM only inside Pro/Con workers | Child workers |
| Validate JSON turn schema | Parent worker |
| Produce verdict file | Supervisor after Parent completes |
| Graceful shutdown on error or completion | Supervisor |
| Progress / IPC event stream | All processes → event queue |

---

## 3. Process topology

```
Main Process (Supervisor)
├── Process: Parent  (_parent_worker)
├── Process: Pro     (_child_worker, role=pro)
└── Process: Con     (_child_worker, role=con)

Queues:
  command_queue      Main → Parent (START / STOP)
  parent_to_pro      Parent → Pro
  pro_to_parent      Pro → Parent
  parent_to_con      Parent → Con
  con_to_parent      Con → Parent
  event_queue        All → Main (GUI / logging)
```

Each debate session creates **fresh processes and queues**. Workers are terminated with `STOP` or process join timeout.

---

## 4. Public API

### `ProcessDebateOrchestrator`

| Method / attribute | Description |
|--------------------|-------------|
| `__init__(config: AppConfig)` | Store config; no processes yet |
| `set_progress_callback(cb: Callable[[str], None])` | Optional hook for GUI |
| `run() -> Path` | Start session; return path to verdict JSON |

### Entry usage

```python
orchestrator = ProcessDebateOrchestrator(config)
orchestrator.set_progress_callback(gui.on_progress)
verdict_path = orchestrator.run()
```

CLI (`debate.main`) and GUI (`debate.gui`) both use this class as of the current codebase.

---

## 5. Parent worker — debate loop

For each `ping` in `1..pings_per_side`:

1. **Pro turn**
   - Put `TURN_REQUEST` on `parent_to_pro` with `{ping, opponent_text=last_con}`.
   - Block on `pro_to_parent` with `request_timeout_seconds`.
   - Validate message: session, type `turn`, sender `pro`, target `parent`, ping match.
   - Call `parent.record_turn(pro_msg)`.
   - Emit progress with truncated text and citation URLs.

2. **Relay to Con**
   - Put `RELAY` on `parent_to_con` with Pro's message (type rewritten to `relay`).

3. **Con turn**
   - Put `TURN_REQUEST` on `parent_to_con` with `{ping, opponent_text=last_pro}`.
   - Validate Con response symmetrically.
   - Relay Con message to Pro for next ping.

4. **Keepalive**
   - Optional keepalive messages if configured interval elapsed (legacy single-process parity).

After all pings:

- Parent worker calls `parent.build_verdict()` (LLM + gatekeeper).
- Verdict returned to supervisor via `command_queue` or shared result channel.
- Supervisor writes `logs/verdict_<session_id>.json`.

---

## 6. Child worker — Pro / Con

Loop until `STOP`:

| Input command | Action |
|---------------|--------|
| `TURN_REQUEST` | Build turn via `ProAgent.build_turn` / `ConAgent.build_turn`; put JSON on `child_to_parent` |
| `RELAY` | Store opponent text for context on next turn |
| `STOP` | Exit loop |

On exception: put `{type: ERROR, role, error}` and emit error event.

Each `build_turn`:

1. Gatekeeper `check(role)` — raise if budget exceeded.
2. LLM call via `LlmClient.prompt(system, user)`.
3. Gatekeeper `record(role)`.
4. Parse / validate JSON into `DebateMessage`.

---

## 7. Message validation rules

Parent worker **must reject** turns that violate:

- Wrong `session_id`
- `type` other than `turn` from children
- `from_role` not matching expected worker
- `to_role` not `parent`
- `payload.ping_number` not matching requested ping
- Missing or malformed payload (Pydantic validation)

Validation failures abort the session with a logged error.

---

## 8. Timeouts and errors

| Condition | Behavior |
|-----------|----------|
| Queue read timeout | `TimeoutError` → session failure, workers stopped |
| Worker ERROR dict | Propagate as `RuntimeError` with role + message |
| Gatekeeper budget exceeded | `BudgetExceededError` in worker → ERROR event |
| LLM failure | Logged in worker; ERROR event; session abort |

Supervisor joins workers with bounded wait; terminates alive workers if needed.

---

## 9. Configuration dependencies

From `config/setup.json` and `config/rate_limits.json`:

| Key | Used for |
|-----|----------|
| `debate.pings_per_side` | Loop bound |
| `debate.request_timeout_seconds` | Queue get timeout |
| `debate.topic`, `pro_side`, `con_side` | Session header / prompts |
| `gatekeeper.*` | Per-worker Gatekeeper instance |
| `llm.*` | LlmClient in each worker |
| `logging.*` | `setup_logging` in each process |

---

## 10. Non-goals (this component)

- Choosing LLM provider (delegated to SDK)
- Parsing environment / loading `.env` (main entry)
- Tkinter rendering (GUI module)
- File-queue / FIFO transport (legacy `DebateOrchestrator`)

---

## 11. Refactor plan (Stage 3)

Split complete under `debate/orchestrator/`:

| Module | Contents |
|--------|----------|
| `supervisor.py` | `ProcessDebateOrchestrator`, session run loop |
| `process_pool.py` | Spawn, stop, restart worker processes |
| `supervisor_watchdog.py` | Process health watchdog |
| `parent_worker.py` | Parent process entry + ping loop |
| `ping_round.py` | Single ping round (pro + con) |
| `child_worker.py` | Pro/Con worker entry |
| `messages.py` | `validate_child_message`, `make_relay` |
| `events.py` | Event queue helpers |
| `commands.py` | IPC command builders |
| `factory.py` | Agent and LLM client factory |
| `verdict_io.py` | Verdict file write + done event |
| `types.py` | Shared type aliases |

**Acceptance:** Each file ≤ 150 code lines; unit tests pass.

---

## 12. Test requirements

| Test | Type |
|------|------|
| Message validation rejects bad ping | Unit |
| Relay rewires type and roles | Unit |
| Full ping loop with mock LLM | Integration |
| Timeout on empty queue | Unit |
| ERROR dict from worker surfaces | Integration |

Existing: `tests/test_process_orchestrator.py` — extend after split.

---

## 13. Success metrics

- Full 10-ping session completes on Windows with Gemini.
- Logs show strict Parent-mediated ordering.
- Verdict JSON valid against `VerdictMessage` schema.
- No direct Pro↔Con queue exists.
