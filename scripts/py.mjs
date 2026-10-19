// Run a Python command inside backend/ with the project venv, on any OS:
//   node scripts/py.mjs -m pytest
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { backend, venvPython } from "./paths.mjs";

if (!existsSync(venvPython)) {
  console.error("backend/.venv not found. Run `npm run setup` first.");
  process.exit(1);
}
const r = spawnSync(venvPython, process.argv.slice(2), { cwd: backend, stdio: "inherit" });
process.exit(r.status ?? 1);
