# local-agent-self-harness

Bringing a local LLM to life as an agent: it designs its own tools inside an offline Docker sandbox, and a human reviews and approves every capability it gains.

> **Status: early and experimental.** The agent has a handful of basic tools and is working through its first "levels". Nothing here is a finished product. It's a learning project, built in public.

## The idea

A language model on its own can only produce text. Everything else an "agent" does comes from the **harness** around it: the instructions, the tools, and the memory it can use.

This project starts with a bare model and **no tools at all**. The agent (named *Muse*) is told the truth about its situation: its weights are fixed, its harness is its "shape", and the harness is the only thing that can change. Its job is to work out what it needs, write the code for it, and explain why. Then I review the code and decide whether it gets installed.

The interesting question: **how much does an agent's behavior change from scaffolding alone, with the weights untouched?**

## How it works

```
 Mac (host)                         Docker (internal network, no internet)
┌──────────────┐                   ┌─────────────────────────────────────┐
│   Ollama     │◀── socat proxy ───│  agent container                    │
│ muse-glimmer │   (only way out)  │   kernel.py: chat loop + memory     │
│ :30b-mlx     │                   │   /workspace (writable)             │
└──────────────┘                   │     core/            read-only      │
                                   │     tools/approved/  read-only      │
                                   │     tools/proposed/  agent writes   │
                                   │     memory/          agent writes   │
                                   └─────────────────────────────────────┘
```

- **Model:** `muse-glimmer:30b-mlx`, running in Ollama on the host. Docker on a Mac has no GPU access, so the model stays outside and the container reaches it through the proxy.
- **Kernel** ([self_iter/agent/kernel.py](self_iter/agent/kernel.py)): a small fixed loop built on the OpenAI Agents SDK. It loads the instructions and approved tools, keeps conversation memory in SQLite, and supports `/reload` and `/exit`.
- **Instructions** ([self_iter/workspace/core/prompt.md](self_iter/workspace/core/prompt.md)): who Muse is, what it can and can't do, and the format for proposing a tool.
- **Challenges** ([self_iter/workspace/challenges.md](self_iter/workspace/challenges.md)): a list of things Muse can't do yet, roughly easiest first, which guides what it builds next.

## The approval loop

1. Muse decides it needs an ability and writes the complete tool code in its reply.
2. I read the code. This is the safety step.
3. If it's acceptable, I save it to `tools/approved/` and run `/reload`.
4. Muse now has the tool. Its tool list is the source of truth for what it can do.

Muse can't edit its own instructions or approved tools. Only I can.

## Safety design

The goal is that a mistake or a prompt injection can't reach my machine. The container is configured so that:

| Control | How |
|---|---|
| No internet | Agent sits only on an `internal: true` Docker network |
| One way out | A socat proxy forwards a single port to Ollama and nothing else |
| Can't rewrite its rules | `core/` and `tools/approved/` are mounted read-only |
| Locked-down container | Read-only root filesystem, all Linux capabilities dropped, no privilege escalation |
| Resource caps | 2 GB RAM, 2 CPUs, 256 processes |
| Human gate | Nothing becomes a tool until I move it into `approved/` |

**Limits to be honest about:** Docker is a strong boundary but not a perfect one, and a reviewer can miss things in code. Ollama is deliberately not exposed on all network interfaces (`0.0.0.0`) to make this easier.

## Run it

Requirements: Ollama with the model pulled, and Docker (I use OrbStack).

```bash
cd self_iter
docker compose up -d --build      # starts the Ollama proxy
docker compose run --rm agent     # starts an interactive session with Muse
```

The kernel is interactive, so use `run` and not `up` for the agent, since it needs a terminal attached.

## Working in the open

This repo is also a record of how I work with AI. The history is meant to be read:

- I commit before each session and read `git diff` after, so anything Muse wrote is visible.
- Approving a tool is its own commit, so the log shows what was proposed, reviewed and accepted.
- [transition.md](transition.md) holds the earlier session notes from learning the basic tool-use loop by hand with curl and Python.

## Background

This started as a hands-on way to understand the agent loop (send messages and tool schemas, check `finish_reason`, run the requested tool, append the result, repeat) by building it myself against a local model instead of using a pre-built harness.
