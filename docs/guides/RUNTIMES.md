# Supported AI Runtimes

spatial-machines works with any AI coding agent that can read markdown files and execute Python scripts. This guide covers setup for each tested runtime.

## How it works

Every runtime reads an instruction file at the repo root:
- **Claude Code** reads `CLAUDE.md` (has Claude-specific subagent syntax)
- **Everything else** reads `AGENTS.md` (harness-agnostic)

Both files teach the agent the same thing: how to adopt the Lead Analyst role, run the 9-agent pipeline, use the core scripts, and produce deliverables. The only difference is subagent delegation syntax.

## Prerequisites (all runtimes)

1. Python 3.11+ installed and on your PATH
2. Clone the repo and set up a venv:
   ```bash
   git clone https://github.com/spatial-machines/spatial-machines.git
   cd spatial-machines
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. Verify with `python demo.py`

---

## Claude Code (CLI)

The primary development runtime. Full subagent delegation support.

```bash
npm i -g @anthropic-ai/claude-code
cd spatial-machines
claude
```

Claude reads `CLAUDE.md` automatically. Type your spatial question and it runs.

**Desktop app:** Claude Code Desktop works identically. Open the repo folder and start chatting.

---

## Codex CLI (OpenAI)

```bash
npm i -g @openai/codex
cd spatial-machines
codex
```

Codex reads `AGENTS.md`. Same pipeline, same outputs. Subagent delegation works through Codex's native tool calling.

**Codex Desktop:** Open the repo folder in the desktop app. Same experience.

---

## T3 Code

T3 Code is a GUI wrapper for coding agents. It shows a chat interface, file tree, and output browser.

```bash
npx t3
```

Or install the desktop app from [github.com/pingdotgg/t3code](https://github.com/pingdotgg/t3code).

Open the spatial-machines folder in T3 Code. It auto-detects `CLAUDE.md` or `AGENTS.md` depending on which backend you've configured (Claude or Codex). The chat interface and file browser make it easier to inspect outputs without using the terminal.

---

## OpenCode

```bash
# Install from opencode.ai
cd spatial-machines
opencode
```

Reads `AGENTS.md`. Works the same as Codex CLI.

---

## Cursor / Windsurf / Other IDEs

Open the repo folder in your IDE. The agent reads `AGENTS.md` from the workspace root.

For Cursor: use Composer mode for best results with multi-file pipeline operations.

---

## Tips for all runtimes

- **Always activate your venv** before starting the agent. The agent runs Python scripts that need geopandas, matplotlib, etc.
- **Start with the demo prompt:** "What does poverty look like in Sedgwick County, Kansas?" This uses bundled data and needs no API keys.
- **Check outputs in your browser:** Open the HTML report the agent produces. Every analysis writes a self-contained HTML file to `outputs/reports/`.
- **PATCH.md:** When you customize the project, your agent should document changes in `PATCH.md`. This is automatic if your agent reads the instruction files.

## Forking and customizing

Every runtime supports the fork-and-customize workflow:
1. Fork the repo on GitHub
2. Clone your fork
3. Ask your agent to make changes (add a data source, change map styles, etc.)
4. Your agent documents each change in `PATCH.md`
5. When upstream releases an update, pull it and ask your agent to re-apply your patches
