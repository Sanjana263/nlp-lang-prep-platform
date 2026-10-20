// One-time project setup: `npm run setup` from the repo root.
// Safe to re-run; it only installs what is missing and never overwrites an existing .env.
import { execFileSync, execSync, spawnSync } from "node:child_process";
import { copyFileSync, existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { randomBytes } from "node:crypto";
import { backend, root, venvPython } from "./paths.mjs";
import { join } from "node:path";

const frontend = join(root, "frontend");
const SUPPORTED = ["3.12", "3.13"]; // spaCy has no wheels for 3.14+ yet

const step = (msg) => console.log(`\n\x1b[36m==> ${msg}\x1b[0m`);
const run = (cmd, args, cwd) => execFileSync(cmd, args, { cwd, stdio: "inherit" });
const npmInstall = (cwd) => execSync("npm install", { cwd, stdio: "inherit" }); // npm is a .cmd on Windows, needs a shell

function pythonVersion(cmd, args = []) {
  const r = spawnSync(cmd, [...args, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"], { encoding: "utf8" });
  return r.status === 0 ? r.stdout.trim() : null;
}

// Prefer the Windows launcher (py -3.12), then versioned binaries, then plain python
function findPython() {
  const candidates = [
    ...SUPPORTED.map((v) => ["py", [`-${v}`]]),
    ...SUPPORTED.map((v) => [`python${v}`, []]),
    ["python3", []],
    ["python", []],
  ];
  for (const [cmd, args] of candidates) {
    if (SUPPORTED.includes(pythonVersion(cmd, args))) return [cmd, args];
  }
  return null;
}

// 1. Backend virtualenv on a supported Python (an old venv on 3.14+/3.15 is rebuilt)
const venvVersion = existsSync(venvPython) ? pythonVersion(venvPython) : null;
if (!SUPPORTED.includes(venvVersion)) {
  const python = findPython();
  if (!python) {
    console.error(
      `\nPython ${SUPPORTED.join(" or ")} is required for the backend (spaCy does not support newer versions yet).\n` +
        "Install Python 3.12 from https://www.python.org/downloads/ (it can sit next to your current Python),\n" +
        "then re-run `npm run setup`.\n"
    );
    process.exit(1);
  }
  if (venvVersion) {
    step(`Removing backend/.venv (Python ${venvVersion} is not supported)`);
    rmSync(join(backend, ".venv"), { recursive: true, force: true });
  }
  step(`Creating backend/.venv with Python ${pythonVersion(...python)}`);
  run(python[0], [...python[1], "-m", "venv", ".venv"], backend);
}

step("Backend: installing packages and the spaCy model (first run downloads ~500 MB)");
run(venvPython, ["-m", "pip", "install", "--upgrade", "pip", "--quiet"], backend);
run(venvPython, ["-m", "pip", "install", "-r", "requirements.txt"], backend);

step("Frontend: installing npm packages");
npmInstall(root);
npmInstall(frontend);

// 2. backend/.env with a freshly generated JWT secret
const envPath = join(backend, ".env");
if (!existsSync(envPath)) {
  step("Creating backend/.env");
  copyFileSync(join(backend, ".env.example"), envPath);
  const secret = randomBytes(48).toString("base64url");
  writeFileSync(envPath, readFileSync(envPath, "utf8").replace(/^JWT_SECRET=.*$/m, `JWT_SECRET=${secret}`));
}

// 3. Migrations, once the database URLs are filled in
if (/USER:PASSWORD|ep-xxxx/.test(readFileSync(envPath, "utf8"))) {
  console.log(
    "\n\x1b[33mAlmost done.\x1b[0m Put your Neon connection strings in backend/.env\n" +
      "(DATABASE_URL = pooled, DIRECT_URL = direct), then run:  npm run dev"
  );
} else {
  step("Applying database migrations");
  run(venvPython, ["-m", "alembic", "upgrade", "head"], backend);
  console.log("\n\x1b[32mSetup complete.\x1b[0m Start everything with:  npm run dev");
}

// 4. Speaking practice needs two free cloud keys (optional for everything else)
if (!/^GROQ_API_KEY=\S/m.test(readFileSync(envPath, "utf8"))) {
  console.log(
    "\nFor speaking practice, add GROQ_API_KEY, HF_TOKEN and HF_SPEECH_SPACE to backend/.env\n" +
      '(free; see "Speaking setup" in README.md). Everything else works without them.'
  );
}
