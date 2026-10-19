import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const root = join(dirname(fileURLToPath(import.meta.url)), "..");
export const backend = join(root, "backend");
export const venvPython =
  process.platform === "win32"
    ? join(backend, ".venv", "Scripts", "python.exe")
    : join(backend, ".venv", "bin", "python");
