#!/usr/bin/env node

import fs from "node:fs";
import { spawn } from "node:child_process";

const action = process.argv[2];
const extraArgs = process.argv.slice(3);

const COMMANDS = {
  build: ["next", ["build"]],
  start: ["next", ["start"]],
  lint: ["next", ["lint"]],
  "i18n:check": ["node", ["./i18n/check/i18n-check.mjs"]],
  "test:frontend": ["vitest", ["run"]],
  "test:frontend:watch": ["vitest", []],
  "test:e2e": ["playwright", ["test"]],
  "test:e2e:ui": ["playwright", ["test", "--ui"]],
  "type-check": ["tsc", ["--noEmit"]],
};

function isDockerRuntime() {
  return fs.existsSync("/.dockerenv") || process.env.RUNNING_IN_DOCKER === "1";
}

function failDockerOnly() {
  console.error(
    [
      "[docker-only] Frontend npm scripts are disabled on the host.",
      "[docker-only] Run them through Docker Compose instead.",
      "[docker-only] Examples:",
      "  cd infra && docker compose --env-file .env run --rm frontend-tests npm run lint",
      "  cd infra && docker compose --env-file .env run --rm frontend-tests npm run test:frontend",
      "  cd infra && docker compose --env-file .env run --rm frontend-tests npm run type-check",
    ].join("\n"),
  );
  process.exit(1);
}

if (!isDockerRuntime()) {
  failDockerOnly();
}

const target = COMMANDS[action];
if (!target) {
  console.error(`[docker-only] Unknown frontend script action: ${action ?? "<missing>"}`);
  process.exit(1);
}

const [command, args] = target;
const child = spawn(command, [...args, ...extraArgs], {
  stdio: "inherit",
  env: process.env,
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});