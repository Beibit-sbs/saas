#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const ROOT_DIR = process.cwd();
const LOCK_FILE = path.join(ROOT_DIR, ".n" + "ext-dev.lock");

function parseRequestedPort(argv, envPort) {
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "-p" || token === "--port") {
      const value = argv[i + 1];
      if (value && /^\d+$/.test(value)) return Number(value);
    }
    const direct = token.match(/^--port=(\d+)$/);
    if (direct) return Number(direct[1]);
  }
  if (envPort && /^\d+$/.test(String(envPort))) return Number(envPort);
  return 3000;
}

function readCmdline(pid) {
  try {
    const raw = fs.readFileSync(`/proc/${pid}/cmdline`, "utf8");
    return raw.split("\u0000").filter(Boolean).join(" ");
  } catch {
    return "";
  }
}

function readCwd(pid) {
  try {
    return fs.readlinkSync(`/proc/${pid}/cwd`);
  } catch {
    return "";
  }
}

function processAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function findExistingNextDevPid() {
  let entries = [];
  try {
    entries = fs.readdirSync("/proc", { withFileTypes: true });
  } catch {
    return null;
  }

  for (const entry of entries) {
    if (!entry.isDirectory() || !/^\d+$/.test(entry.name)) continue;
    const pid = Number(entry.name);
    if (!Number.isInteger(pid) || pid <= 0 || pid === process.pid) continue;
    const cmdline = readCmdline(pid);
    if (!cmdline || !cmdline.includes("next") || !cmdline.includes("dev")) continue;
    const cwd = readCwd(pid);
    if (cwd && path.resolve(cwd) === path.resolve(ROOT_DIR)) {
      return pid;
    }
  }

  return null;
}

function readLock() {
  try {
    const raw = fs.readFileSync(LOCK_FILE, "utf8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function writeLock(lock) {
  fs.writeFileSync(LOCK_FILE, `${JSON.stringify(lock, null, 2)}\n`, "utf8");
}

function removeLockSafe() {
  try {
    const lock = readLock();
    if (lock && Number(lock.pid) !== process.pid) return;
    fs.unlinkSync(LOCK_FILE);
  } catch {
    // Ignore cleanup errors.
  }
}

function printFailure({ pid, port, source }) {
  const parts = [
    "\n[dev-guard] Another frontend dev instance is already running.",
    `[dev-guard] Source: ${source}`,
    pid ? `[dev-guard] Existing PID: ${pid}` : "[dev-guard] Existing PID: unknown",
    port ? `[dev-guard] Requested port: ${port}` : "[dev-guard] Requested port: unknown",
    "[dev-guard] Stop the existing dev server before starting another instance.\n",
  ];
  console.error(parts.join("\n"));
}

function recoverStaleLock(lock) {
  const pid = Number(lock?.pid || 0);
  if (!pid || !processAlive(pid)) {
    try {
      fs.unlinkSync(LOCK_FILE);
      console.warn("[dev-guard] Removed stale lock file.");
    } catch {
      // Ignore stale-lock cleanup race.
    }
    return true;
  }

  const cwd = readCwd(pid);
  if (!cwd || path.resolve(cwd) !== path.resolve(ROOT_DIR)) {
    try {
      fs.unlinkSync(LOCK_FILE);
      console.warn("[dev-guard] Removed foreign lock file.");
    } catch {
      // Ignore stale-lock cleanup race.
    }
    return true;
  }

  return false;
}

function acquireLock(requestedPort) {
  try {
    const fd = fs.openSync(LOCK_FILE, "wx");
    fs.closeSync(fd);
    writeLock({
      pid: process.pid,
      requestedPort,
      rootDir: ROOT_DIR,
      createdAt: new Date().toISOString(),
    });
    return true;
  } catch {
    const lock = readLock();
    if (lock && recoverStaleLock(lock)) {
      return acquireLock(requestedPort);
    }
    printFailure({
      pid: lock?.pid,
      port: lock?.requestedPort,
      source: "lock-file",
    });
    return false;
  }
}

const argv = process.argv.slice(2);
const requestedPort = parseRequestedPort(argv, process.env.PORT);

const existingPid = findExistingNextDevPid();
if (existingPid) {
  printFailure({
    pid: existingPid,
    port: requestedPort,
    source: "process-scan",
  });
  process.exit(1);
}

if (!acquireLock(requestedPort)) {
  process.exit(1);
}

let child = null;
function shutdown(code = 0) {
  if (child && !child.killed) {
    child.kill("SIGTERM");
  }
  removeLockSafe();
  process.exit(code);
}

process.on("SIGINT", () => shutdown(130));
process.on("SIGTERM", () => shutdown(143));
process.on("exit", () => removeLockSafe());
process.on("uncaughtException", (error) => {
  console.error(error);
  shutdown(1);
});

child = spawn("next", ["dev", ...argv], {
  stdio: "inherit",
  env: process.env,
});

child.on("exit", (code, signal) => {
  removeLockSafe();
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
