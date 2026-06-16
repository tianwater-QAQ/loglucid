// Lucid Logs — a thin VS Code / Cursor wrapper around the `loglucid feed` CLI.
//
// One command, "Lucid: Feed recent logs to AI": it takes your current logs (the
// selection, else the active file, else a file you pick), pipes them through
// `loglucid feed` (de-noise + redact secrets + token budget), and copies the
// result to the clipboard so you can paste it into your AI chat.
//
// Cursor is a VS Code fork, so this one extension works in both.

const vscode = require("vscode");
const { spawn } = require("child_process");

function getConfig() {
  const c = vscode.workspace.getConfiguration("lucid");
  return {
    command: c.get("command", "loglucid"),
    maxTokens: c.get("maxTokens", 2000),
    last: c.get("last", 120),
    redact: c.get("redact", true),
  };
}

// Run `loglucid feed -` feeding `text` on stdin, resolve with stdout.
function runFeed(text, cfg) {
  return new Promise((resolve, reject) => {
    const args = ["feed", "-", "--max-tokens", String(cfg.maxTokens), "--last", String(cfg.last)];
    if (!cfg.redact) args.push("--no-redact");

    let child;
    try {
      // command may be "loglucid" or e.g. "python -m loglucid.cli"
      const parts = cfg.command.split(" ");
      child = spawn(parts[0], parts.slice(1).concat(args), { shell: false });
    } catch (e) {
      return reject(e);
    }

    let out = "";
    let err = "";
    child.stdout.on("data", (d) => (out += d.toString()));
    child.stderr.on("data", (d) => (err += d.toString()));
    child.on("error", (e) =>
      reject(new Error(`could not run '${cfg.command}': ${e.message}. Is loglucid installed?`))
    );
    child.on("close", (code) => (code === 0 ? resolve(out) : reject(new Error(err || `exit ${code}`))));
    child.stdin.write(text);
    child.stdin.end();
  });
}

async function pickLogText() {
  const editor = vscode.window.activeTextEditor;
  if (editor) {
    const sel = editor.selection;
    if (sel && !sel.isEmpty) return editor.document.getText(sel);
    return editor.document.getText();
  }
  const picked = await vscode.window.showOpenDialog({
    canSelectMany: false,
    openLabel: "Feed this log to AI",
    filters: { Logs: ["log", "txt"], All: ["*"] },
  });
  if (!picked || !picked.length) return null;
  const bytes = await vscode.workspace.fs.readFile(picked[0]);
  return Buffer.from(bytes).toString("utf8");
}

function activate(context) {
  const cmd = vscode.commands.registerCommand("lucid.feedLogs", async () => {
    const cfg = getConfig();
    const text = await pickLogText();
    if (text == null) return;
    if (!text.trim()) {
      vscode.window.showWarningMessage("Lucid: no log text to feed.");
      return;
    }
    try {
      const block = await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "Lucid: packing logs…" },
        () => runFeed(text, cfg)
      );
      await vscode.env.clipboard.writeText(block);
      const lines = block.split("\n").length;
      vscode.window.showInformationMessage(
        `Lucid: ${lines} lines copied (redacted, ≤${cfg.maxTokens} tokens). Paste into your AI chat.`
      );
    } catch (e) {
      vscode.window.showErrorMessage(`Lucid: ${e.message}`);
    }
  });
  context.subscriptions.push(cmd);
}

function deactivate() {}

module.exports = { activate, deactivate };
