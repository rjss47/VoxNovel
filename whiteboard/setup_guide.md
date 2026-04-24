# Setup Guide for Kokoro TTS

This document outlines the steps to set up Kokoro TTS locally for the VoxNovel POC.

## 1. Check Python Version
Machine Learning libraries (like PyTorch, which Kokoro uses) can sometimes be slow to support the absolute newest Python versions. Your `pyproject.toml` currently requires `>=3.14`. 
If you run into installation errors, you may need to drop your Python version down to `3.12` or `3.11`.

## 2. Install Packages
Since you have a `pyproject.toml`, I assume you might be using **uv**. Run this command in your terminal to add the dependencies:

```bash
uv add kokoro soundfile
```

*(If you are using standard pip, run: `pip install kokoro soundfile`)*

> **Note:** We only need `soundfile` to save the generated audio to a `.wav` file. We can concatenate the audio directly using `numpy` (which is installed automatically with Kokoro), so we don't need `pydub` or `ffmpeg`!

## 3. Download Voices (Optional but recommended)
The `kokoro` package comes with some default capabilities, but it will automatically fetch the model weights (`~82MB`) the first time you run it. It also automatically fetches voice profiles when you specify them in the code.

For our project, we will use:
- `am_adam` (American Male) for **Elias**
- `af_bella` (American Female) for **Sarah**

## 4. System Requirement (espeak-ng)
Kokoro relies on `espeak-ng` to convert text into phonemes (the sounds of the words) before turning it into audio. 
Since you are on Windows, the Python package usually handles this or uses a pure Python fallback, but if you get an `espeak` error later, you might need to install the `espeak-ng` Windows installer. We will cross that bridge if we get an error!

---
**Next Steps:** Once you have run the installation command, let me know, and I will generate the Python script!
