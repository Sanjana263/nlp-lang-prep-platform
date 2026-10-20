---
title: Cadence Speech
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
pinned: false
license: mit
short_description: Phoneme-level pronunciation scoring for Cadence
---

# Cadence pronunciation checker

Runs the pronunciation step of the Cadence speaking assessment on a free ZeroGPU GPU:
a wav2vec2 phoneme recogniser (`facebook/wav2vec2-xlsr-53-espeak-cv-ft`) plus espeak-ng
expected phonemes and CTC forced alignment.

Deploy and update it from the Cadence repo with `python -m scripts.deploy_speech_space`
(run in `backend/`). The `speaking/` folder here is copied from `backend/app/speaking/`;
edit it there, not here.
