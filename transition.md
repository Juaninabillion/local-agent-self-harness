# Harness Training — Session Transition Notes

Context to pick this project back up in VS Code / a new Claude Code session.

## Goal

Building a local agentic AI harness — running a local LLM (not a paid API) and writing
the tool-use loop ("agent harness") around it by hand, to follow along with the book
**"The Bible of Agentic AI Systems"** (which teaches this pattern using the OpenAI SDK
against OpenAI's hosted API). The plan is to swap the hosted API for a local Ollama
model and build the same kind of harness — for learning, and to avoid burning paid
API usage while experimenting.

## Machine specs (checked this session)

- Chip: Apple M5 Pro (18-core: 6 Super + 12 Performance)
- Memory: 48 GB unified
- Free disk: ~611 GB
- macOS 26.5.1
- Plenty of headroom for local models up to ~30-32B parameters (quantized).

## Model chosen: `muse-glimmer:30b-mlx`

Already pulled via Ollama (~19GB on disk, confirmed with `ollama list`).

Why this one (researched live on ollama.com's library, sorted by newest — a lot of
this is newer than Claude's Jan 2026 knowledge cutoff so it was worth checking live):
- Meta model, released ~3 weeks before this session, explicitly "built for always-on
  local agents... tuned for tool use, long tasks, and failure recovery"
- Has a native MLX build optimized for Apple Silicon (`:30b-mlx` tag) — faster on M-series
  chips than a generic GGUF
- Supports tool/function calling and has a visible "reasoning" trace separate from its
  final answer (a `thinking`-tagged model)
- No known macOS issues (unlike the runner-up candidate, `laguna-xs-2.1`, which had an
  open/unresolved macOS bug disclosed in its own README at the time — worth rechecking
  if we ever revisit it)
- Runner-up alternatives if we want to compare later: `qwen3.8:27b` (very established,
  2.3M+ pulls), `granite4.2:8b` (smaller, IBM, reliable tool-calling)

Also discovered along the way: Ollama has a built-in `ollama launch` command
(`ollama launch opencode --model <model>`) that auto-configures existing agent CLIs
(OpenCode, Claude Code, Codex, Droid) to run against a local model with zero config.
This is a *pre-built* harness (skips writing the loop yourself) — noted as an option
but the user wants to hand-build the harness instead, matching the book's approach.

## Prior project (not used going forward, per user's choice)

There's an earlier practice project at `~/code/local-ai-lab` (git-initialized,
2026-09-13) with:
- `call_local_model.py` — direct OpenAI-SDK-style calls to Ollama
- `mcp_local_llm_server.py` — an MCP server that exposes the local model as MCP tools
  (`ask_local_model`, `list_local_models`) — note this is the *reverse* direction of
  what we're building now (it lets an MCP client like Claude Code call out to the local
  model as a tool, rather than giving the local model tools of its own)
- `test_mcp_client.py`, `requirements.txt`, `.venv`

User explicitly chose to **start fresh** in this new directory rather than migrate that
project. `~/code/local-ai-lab` is untouched and can be referenced if useful, but this
new directory (`~/Documents/Harness_training`) has nothing in it yet except this file.

## Core concepts covered this session (user is learning, wanted things explained, not just built)

Established the 3-layer mental model:

1. **The model weights** — an inert file, does nothing by itself.
2. **Ollama** — the inference engine + API server. Loads the weights, exposes an
   OpenAI-compatible endpoint at `http://localhost:11434/v1`. It can run the model and
   relay whatever text/JSON it produces, but has **no tools of its own** — no file
   access, no shell, nothing.
3. **The agent harness** (the missing piece, not yet built) — ordinary code that:
   1. Sends the conversation to the model (with a list of available tools described
      as JSON schemas)
   2. Checks `finish_reason` in the response: `"stop"` = normal answer;
      `"tool_calls"` = the model wants to invoke a tool
   3. If `"tool_calls"`: parses `message.tool_calls[0].function.arguments` (comes back
      as a **JSON string**, needs `json.loads()`), actually executes the real tool in
      Python (e.g. real file read, real shell command)
   4. Appends the assistant's tool-call message *and* a new `role: "tool"` message
      (with matching `tool_call_id`) containing the real result, back onto the
      conversation
   5. Sends the growing message list back to the model, repeat from step 1
   6. Loop ends when the model returns `finish_reason: "stop"` with a real answer

### Hands-on verification done via `curl` against `http://localhost:11434/v1/chat/completions`

- Confirmed the raw model (no `tools` param) correctly says it can't read local files —
  it's aware it has no hands, doesn't hallucinate access.
- Confirmed that passing a `tools` array (a `read_file` function schema) and asking it
  to read a real file (`call_local_model.py`) causes the model to respond with
  `finish_reason: "tool_calls"` and an empty `content`, plus a `tool_calls` array
  requesting `read_file(path="call_local_model.py")` — proving the model can *ask* for
  a tool but **nothing executes it** without a harness (curl just prints the request
  and stops).
- Started (but didn't finish — ran out of time) the manual capstone: feeding a fake
  `role: "tool"` message back into a follow-up `curl` call, playing the role of the
  harness by hand, to see the model produce a final real answer once given the real
  tool result. **This is the natural next hands-on step when picking this back up.**

### Response JSON anatomy (from the OpenAI-compatible endpoint)

```
choices[0].message.content      -> the actual reply text
choices[0].message.reasoning    -> the "thinking" trace (separate from content)
choices[0].message.tool_calls   -> array of {id, function:{name, arguments}} when present
choices[0].finish_reason        -> "stop" or "tool_calls" (the key signal to branch on)
usage.prompt_tokens_details.cached_tokens -> Ollama caches repeated prompt prefixes
```

## Practical operational notes

- Ollama does **not** always auto-start after a reboot. If `ollama list` fails to
  connect: open the Ollama menu-bar app, or run `ollama serve` in a dedicated terminal
  tab and leave it running.
- Pulled models persist on disk across reboots — no need to re-pull `muse-glimmer:30b-mlx`
  unless it's removed.
- `ollama pull` resumes partial downloads if interrupted (verified after a laptop crash
  mid-download).

## Not yet done — next steps

1. Finish the manual `curl` capstone exercise (feed back a real tool result by hand,
   see the model produce a grounded final answer) — good to do once, for intuition,
   before writing code.
2. Write the actual Python harness (~50-100 lines): OpenAI SDK client pointed at
   `http://localhost:11434/v1`, a small set of real tools (start with `read_file`,
   maybe `run_shell`), and the loop described above.
3. Compare against the book's chapters, which use the hosted OpenAI API — the harness
   code should be nearly identical except for `base_url`/`api_key` and tool execution.
4. User wants to *see file changes happen in real time*, hence the move to VS Code —
   worth using VS Code's file explorer / diff view alongside whatever agent (Claude
   Code, or a hand-rolled script) is editing files here.

## User working style notes

- Wants concepts explained, not just implemented — has been doing hands-on `curl`/
  `ollama run` exercises rather than having code written for them.
- At one point explicitly said: "tell me what to do, don't do it for me" — prefers
  step-by-step instructions to run themselves over having actions taken automatically,
  especially for learning-oriented steps. Worth defaulting to this mode unless they ask
  for something to just be built.
- Has limited time in some sessions — comfortable pausing mid-exercise and resuming
  later.
