# Lucid Logs — VS Code / Cursor extension

One command — **"Lucid: Feed recent logs to AI"** — turns your current logs into a
clean, **redacted**, token-budgeted block on your clipboard, ready to paste into
ChatGPT / Claude / Cursor's chat. It's a thin wrapper around the
[`loglucid feed`](https://github.com/tianwater-QAQ/loglucid) CLI, so VS Code and
Cursor (a VS Code fork) both work with the same extension.

## What it does

1. Takes your logs: the current **selection**, else the **active file**, else a file
   you pick.
2. Pipes them through `loglucid feed -` → de-noise + secret/PII redaction + token budget.
3. Copies the result to the clipboard and tells you how many tokens it is.

## Prerequisite

Install the CLI so the extension can call it:

```bash
pip install loglucid
loglucid --help        # confirm it's on PATH
```

If `loglucid` isn't on your PATH, set **`lucid.command`** in settings (an absolute
path, or e.g. `python -m loglucid.cli`).

## Run it (dev / test)

This MVP isn't published to the Marketplace yet — run it from source:

1. `cd editors/vscode`
2. Open that folder in VS Code or Cursor.
3. Press **F5** → an *Extension Development Host* window opens with Lucid loaded.
4. Open a log file (or select some log lines), then run **Lucid: Feed recent logs to AI**
   from the Command Palette (`Ctrl/Cmd+Shift+P`).
5. Paste the clipboard into your AI chat.

To package a `.vsix`: `npm i -g @vscode/vsce && vsce package`.

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `lucid.command` | `loglucid` | CLI command (or absolute path / wrapper) |
| `lucid.maxTokens` | `2000` | Token budget for the block |
| `lucid.last` | `120` | Recent lines to consider |
| `lucid.redact` | `true` | Redact secrets/PII before logs leave your machine |

## Roadmap

- Insert directly into Cursor's AI chat (not just clipboard) once a stable API exists.
- Pull from the integrated terminal buffer.
- A status-bar button.
