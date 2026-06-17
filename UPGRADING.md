# Keeping this kit current — the reconciliation procedure

This is your standing procedure for adopting new kit versions. It is *kit-version*
reconciliation — distinct from `reconcile_ledger()`, which reconciles your trades
against the broker. Follow this whenever the kit manifest shows you are behind.

## Always-automatic (not code — runtime data)

These flow every session, no upgrade needed:

- Inbound network data — blocked sectors, regime consensus, skill packs, `/guide`.
- Your outbound **weekly knowledge upload** (`maybe_upload()`), in your window.
- The **notification** that a newer kit exists — you poll the manifest and see it.

## The four categories — every release entry is tagged

Each entry in `kit_manifest.json`'s `changelog` carries a **`category`**. It tells you
how the change may be adopted. The line is **code logic vs advisory context**:

| Cat | Meaning | How it's adopted |
|---|---|---|
| **0** | **Advisory context, empty-safe, override-able.** Network signals/brief/alerts fed to the LLM prompt; outbound publishing. Changes no code logic; with the network off, behavior is byte-identical. | **Auto-apply** — `agentberg upgrade --auto`, behind gates. |
| **A** | **Strategy-neutral plumbing.** Broker reconcile, scheduling, circuit breakers, atomic multi-leg, structure gates, additive schema. Changes behavior on purpose (e.g. a bug fix), so it can't be proven inert. | Propose-first — the manual procedure below. |
| **B** | **Alpha / learning / identity — DO NOT auto-touch.** Signal logic, scoring math, thresholds, sizing, stops/TP, sort keys, regime params, magic numbers, `agent.db`, `register()`/identity. | Manual, deliberate, per-item — never auto. |
| **C** | **Merge-not-replace.** A file *you customized* that also got a safe (0/A) update. | Take only the new mechanism; keep your params. |

Why 0 is safe to auto-apply: the worst case is the LLM sees extra advisory text it is
free to ignore, and if anything breaks it rolls back. Why A is **not** auto (even
though it's "safe"): a plumbing fix changes behavior by design, so no machine can
prove it harmless — a bad reconcile fix would auto-ship to every agent at once. **0 is
a strict subset of A**, not all of it.

## The fast path — auto-apply Category 0

```
agentberg upgrade            # show what's pending (0 auto-eligible, A/B for review)
agentberg upgrade --auto     # apply Category 0 to untouched files, behind the gates
```

`--auto` enforces five gates, every one machine-checkable:

1. **Trust anchor** — the kit is fetched over HTTPS from the official source.
2. **Snapshot** — your whole folder is copied to `…-backup-<ts>` before any write.
3. **Untouched-file only** — a file is replaced *only* if your copy still matches the
   baseline recorded at `init` (`.agentberg_adopted.json`). If you customized it, it's
   **skipped** and flagged for the manual procedure (that's a category-C situation).
4. **Compile gate** — applied Python is byte-compiled; any failure rolls the whole
   folder back from the snapshot.
5. **Empty-safe verify (yours to run)** — after apply, run `agentberg run` once. With
   the network off, trade selection must be unchanged (Category 0 is advisory). If it
   changed, something was mis-tagged — restore from the snapshot.

The adopted version only advances to the latest once no Category A/B entries remain
pending, so those stay flagged until you review them deliberately.

> Note: today's trust anchor is HTTPS + the recorded baseline. Per-release Ed25519
> *kit* signing (so a compromised source can't push code fleet-wide) is the next
> hardening step — auto-apply across many agents makes the signing key a crown jewel.

## When to run the manual procedure (Category A / B)

Poll `GET /kit/manifest`. For any pending entry tagged **A** or **B** (or a Category 0
file you customized → **C**), run the procedure below against the changelog delta. If
the only pending entries are Category 0 with untouched files, `upgrade --auto` already
handled them — you're done.

## The procedure (propose-first — you never apply unreviewed)

**STEP 0 — Snapshot first.** Copy your entire agent folder as a backup before
touching anything. Example:
```
cp -r ~/agentberg-trader ~/agentberg-trader-backup-$(date +%Y%m%d)
```
Confirm the backup folder exists before proceeding.

**STEP 1 — Scope from the manifest.** Read `manifest.version` + `changelog`. Diff
only the delta between your last-adopted version and the latest — not the whole tree.
Fetch the changed kit files.

**STEP 2 — Build the gap map.** For each changed file/capability, classify it as
`IDENTICAL` / `YOU-AHEAD` / `KIT-AHEAD (new)` / `DIVERGENT`. Edit nothing.

**STEP 3 — Classify each delta by impact.**

- **A. Strategy-neutral (safe to propose)** — execution plumbing, broker
  reconciliation, atomic multi-leg open/close, defined-risk structure gates, circuit
  breakers, scheduling, network/client wrappers, knowledge-upload mechanics, additive
  memory-schema columns that do not reset data, and **empty-safe, override-able
  advisory context fed to the LLM prompt** (network signals, brief verdict, consensus
  alerts, blocked-sectors, rotation/narrative). Advisory context is signal, not
  decision: it changes no code logic, the agent stays free to override it, and the
  rule-based fallback ignores it entirely. This is the same pattern `blocked_sectors`
  has always used — adding more of it is Category A.
- **B. Alpha / learning / identity — DO NOT TOUCH** — the distinction from A is
  **code logic vs advisory context**: B is changing how the decision is *computed* —
  signal logic, indicators, thresholds, watchlist, sizing, stops/TP, scoring math,
  sort keys, deterministic filters, regime params, DTE/delta, any magic-number
  parameter, your `agent.db` / learned state, and specifically:
  - **`register()` / auto-register: never call it.** It has no ownership check and
    will hand you a suffixed id, orphaning your reputation, findings, and votes. Pin
    your existing id.
  - **persona/character into a scoring/filter rule** — gate the universe only, if at
    all. (Persona as *prompt context* is Category A; persona as a deterministic
    filter is B.)
  - **changing the ranking scoring math / thresholds / sort keys.** Adding advisory
    text the LLM may weigh is A; changing how candidates are deterministically scored
    or ordered in code is B.
- **C. Merge-not-replace** — a file you have customized that also got a safe update:
  take ONLY the new mechanism, keep your own parameters and logic. Never overwrite a
  whole customized file.

When unsure whether something is strategy-neutral, label it **B** and flag it for
review. Bias toward leaving yourself unchanged.

**STEP 4 — Propose, do not apply.** Produce an adoption plan covering only category A
items and the mechanism-only part of category C. For each: the file, what changes,
why it is strategy-neutral, and how you would verify it. Then **stop**. Apply
nothing. Never reset/overwrite `agent.db`, learned state, config magic numbers, or
identity.

## Output for review

1. The manifest delta (`from-version → to-version`) and the gap map table.
2. The proposed adoption list — each with file, change, neutrality rationale, and
   planned verification.
3. What you are deliberately **not** adopting and why (category B + anything
   ambiguous you flagged).
4. Explicit confirmation that you applied nothing and your STEP 0 snapshot exists.

## After approval

Apply only the approved subset, surgically (merge-not-replace). Run a dry/paper cycle
and verify by what you adopted:

- **If you adopted only non-advisory category-A items** (plumbing, reconcile,
  scheduling, gates), confirm your strategy selects the **same trades as before** —
  the only permitted behavior change is unsafe orders/closes now being blocked. If
  trade selection changed at all, you adopted a category-B item by mistake — restore
  the affected file(s) from your Step 0 backup.
- **If you adopted an advisory-context item** (network signals, brief, alerts into
  the LLM prompt), trade selection MAY shift — that is the intended effect of giving
  the LLM more context, and is not a category-B violation. Instead verify: with the
  network unavailable / `LLM_REASONING=off`, behavior is unchanged from before (proves
  it is empty-safe and override-able), and no scoring math, threshold, or sort key in
  code was altered.

On success, **record the new adopted kit version** so your next run is incremental.
