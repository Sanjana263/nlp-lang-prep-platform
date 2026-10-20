"""Create or update the Cadence pronunciation Space on Hugging Face (free ZeroGPU).

Run from backend/ once you have HF_TOKEN (a "write" token) and HF_SPEECH_SPACE in backend/.env:
    python -m scripts.deploy_speech_space

It uploads speech-space/ plus the shared scoring code from app/speaking/, and asks for ZeroGPU
hardware. Re-run it whenever app/speaking/pronunciation.py changes.
"""
import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

from app.core.config import get_settings

BACKEND = Path(__file__).resolve().parents[1]
SPACE_SRC = BACKEND.parent / "speech-space"
SHARED = ["audio.py", "fluency.py", "pronunciation.py"]  # copied into the Space as package "speaking"


def main() -> None:
    settings = get_settings()
    space, token = settings.HF_SPEECH_SPACE, settings.HF_TOKEN
    if not space or "/" not in space or not token:
        sys.exit("Set HF_TOKEN and HF_SPEECH_SPACE (e.g. your-username/cadence-speech) in backend/.env first.")

    api = HfApi(token=token)
    api.create_repo(space, repo_type="space", space_sdk="gradio", space_hardware="zero-a10g", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        for f in ("app.py", "requirements.txt", "README.md"):
            shutil.copy(SPACE_SRC / f, out / f)
        pkg = out / "speaking"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        for f in SHARED:
            shutil.copy(BACKEND / "app" / "speaking" / f, pkg / f)
        api.upload_folder(repo_id=space, repo_type="space", folder_path=out, commit_message="Deploy from Cadence repo")

    try:
        api.request_space_hardware(space, hardware="zero-a10g")
    except Exception as exc:  # e.g. account too new for ZeroGPU
        print(f"Could not switch the Space to ZeroGPU automatically ({exc}).")
        print(f"Open https://huggingface.co/spaces/{space}/settings and choose ZeroGPU under Space hardware.")

    print(f"Deployed. The Space builds in a few minutes: https://huggingface.co/spaces/{space}")


if __name__ == "__main__":
    main()
