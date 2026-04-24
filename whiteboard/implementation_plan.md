# Simple TTS Proof of Concept (POC) Plan

This plan outlines the steps to build a lightweight, locally run Text-to-Speech (TTS) system that parses `sample.txt`, assigns specific voices to Elias and Sarah, and generates a complete audio file of the dialogue.

## Model Recommendation: Kokoro TTS

For this POC, I strongly recommend using **Kokoro TTS**. 
- **Why?** It is currently the state-of-the-art for lightweight, local TTS. At only ~82M parameters, it runs extremely fast on standard CPUs and provides incredibly natural-sounding, high-quality voices (unlike older robotic TTS systems). 
- **Alternative:** **Piper TTS** is also a great option if you need something even lighter, but Kokoro provides superior audio quality while remaining very easy to set up via Python.

## Proposed Implementation Steps

1.  **Environment Setup**
    - Ensure Python dependencies are installed. We will need: `kokoro`, `soundfile` (for saving audio), and `pydub` (for concatenating audio files easily).
    - Download the lightweight Kokoro model weights and a couple of default voice profiles (e.g., one male voice for Elias, one female voice for Sarah).

2.  **Dialogue Parsing Module**
    - Read `sample.txt`.
    - Parse the text line by line to extract the speaker name and the dialogue text.
    - *Example:* `Sarah: Elias? Are you actually up here?` -> Speaker: `Sarah`, Text: `Elias? Are you actually up here?`

3.  **Voice Assignment & Generation**
    - Map speakers to specific voice profiles:
        - `Elias` -> `am_adam` (or a similar male voice profile in Kokoro)
        - `Sarah` -> `af_bella` (or a similar female voice profile in Kokoro)
    - Loop through the parsed dialogue and generate temporary audio segments for each line using the assigned voice.

4.  **Audio Concatenation**
    - Combine all the sequential audio segments into a single, cohesive audio file (`final_dialogue.wav`).
    - Add a tiny pause (e.g., 0.2 seconds) between dialogue lines to make the conversation sound natural.

## User Review Required

> [!IMPORTANT]  
> Please review the choice of TTS engine. 
> - Are you happy to proceed with **Kokoro TTS** for high-quality local generation? 
> - Would you prefer we stick to standard Python libraries (like `pyttsx3` or `gTTS`) even if the quality is lower/requires internet, just for the absolute simplest setup?

## Open Questions

> [!NOTE]
> 1. Do you have a specific Python package manager preference for this project (e.g., `uv`, `pip`, `poetry`)? I see a `pyproject.toml` and `.python-version` in the directory.
> 2. Do you want the final audio file saved in a specific format (e.g., `.wav` or `.mp3`)?
