"""Cadence pronunciation checker: a Hugging Face ZeroGPU Space.

The Cadence backend sends a recording plus the word timings from speech-to-text, and gets
back phoneme-level pronunciation results. The scoring code is copied in from
backend/app/speaking/ by backend/scripts/deploy_speech_space.py, so there is one source of truth.

Only the neural network runs on the GPU (a few seconds per answer); the phoneme alignment
runs on the Space's CPU, so each call uses as little of the caller's daily GPU quota as possible.
"""
import json

import gradio as gr
import spaces

from speaking import pronunciation
from speaking.audio import load_audio
from speaking.fluency import Word

MODEL = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"

# ZeroGPU: load once and place on CUDA at startup; a real GPU is attached only inside @spaces.GPU.
model, _processor = pronunciation._load(MODEL)
model.to("cuda")
pronunciation.expected_phones(["hello"])  # start espeak-ng once


# 60 s is the ceiling, not the charge: quota counts only the time actually used. The first call
# after a cold start also attaches the GPU and moves the model onto it, which takes a while.
@spaces.GPU(duration=60)
def _log_probs(audio, words):
    return pronunciation.phone_log_probs(audio, words, MODEL)


def assess(audio_path: str, words_json: str) -> str:
    audio = load_audio(audio_path)
    words = [
        Word(text=w["text"], start=float(w["start"]), end=float(w["end"]), filler=bool(w.get("filler")))
        for w in json.loads(words_json)
    ]
    lp = _log_probs(audio, words)
    result = pronunciation.assess(audio, words, MODEL, lp=lp)
    return json.dumps(result.to_dict(), ensure_ascii=False)


with gr.Blocks(title="Cadence pronunciation checker") as demo:
    gr.Markdown(
        "# Cadence pronunciation checker\n"
        "API for the Cadence IELTS practice platform. It takes a recording and the word timings "
        "from speech-to-text and returns, for each word, which sounds were said clearly."
    )
    audio_in = gr.Audio(type="filepath", label="Recording")
    words_in = gr.Textbox(label="Words with timings (JSON)", lines=4)
    result_out = gr.Textbox(label="Result (JSON)", lines=8)
    gr.Button("Check pronunciation").click(assess, [audio_in, words_in], result_out, api_name="assess")

demo.queue(max_size=20).launch(show_error=True)  # send real error messages to the caller
