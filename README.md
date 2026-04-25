# 1. The Vision

To transform static digital novels into immersive, multi-character audio experiences ("Automated Radio Plays") using local AI. The system will move beyond standard text-to-speech by incorporating:

- **Dialogue Attribution**: Identifying who is speaking.
- **Emotional Intelligence**: Tagging text with emotional context (rage, whisper, joy).
- **Character Consistency**: Unique, persistent voices for every character.
- **Visual Sync**: Real-time text highlighting synchronized with the audio.

---

## 2. System Architecture (The "Sequential Pipeline")

To accommodate the **4GB VRAM limit**, the system is designed as a non-concurrent pipeline. Only one heavy model (LLM or TTS) will reside in the GPU memory at a time.

### Stage 1: The Scripter (NLP & Attribution)

- **Input**: Raw `.epub` or `.txt`.
- **Process**:
    - Clean text and identify scene breaks.
    - **Heuristic Pass**: Use Regex/spaCy for simple "said John" attributions.
    - **LLM Pass**: Use **Llama 3.2 (1B/3B)** via Ollama to resolve ambiguous dialogues and assign emotional tags.
- **Output**: `script.json` (A sequence of lines with Speaker, Text, and Emotion tags).

### Stage 2: The Casting Director (Voice Mapping)

- **Process**:
    - Analyze the frequency of characters in `script.json`.
    - Assign each character a "Voice Latent" (a digital fingerprint) from a local library of archetypes.
    - Ensure the "Narrator" has a distinct, neutral, but engaging tone.
- **Output**: Updated `character_map.json`.

### Stage 3: The Recording Studio (Synthesis)

- **Process**:
    - Load **XTTSv2** into GPU VRAM.
    - Iterate through `script.json`. Generate a short `.wav` file for every line.
    - Use "Reference Audio" clips to inject the LLM-defined emotions into the speech.
- **Output**: A folder containing hundreds of numbered `.wav` files and a `sync_map.json` (timing data).

### Stage 4: The Sound Engineer (Post-Processing)

- **Process**:
    - Use **FFmpeg** to stitch audio files.
    - Apply "Smart Padding" (variable silences based on punctuation and speaker changes).
    - Normalize volume levels across different character voices.
- **Output**: Final `.mp3` or `.m4b` file + Sync-Map for the UI.

---

## 3. Technical Stack (Local & Free)

| Component | Technology | Reasoning |
| --- | --- | --- |
| **Orchestration** | Python 3.10+ | Industry standard for AI glue-code. |
| **LLM (Director)** | Llama 3.2 (via Ollama) | High performance on low RAM/VRAM. |
| **TTS (Actor)** | XTTSv2 (Coqui) | Best-in-class local cloning and emotion. |
| **Audio Engine** | FFmpeg / Pydub | Robust, programmatic audio manipulation. |
| **Data Storage** | SQLite / JSON | Simple, local, no-overhead persistence. |

---

## 4. Hardware Optimization Strategy (The 4GB VRAM Hack)

1. **Stage-Gating**: We will write a "Janitor" script that clears the GPU cache between Stage 1 and Stage 3 to prevent "Out of Memory" (OOM) errors.
2. **Quantization**: We will use 4-bit or 8-bit versions (GGUF/EXL2) of models to ensure they fit in the 3050’s memory.
3. **Sub-Sampling**: Instead of processing a 100,000-word book in one go, we will process it in **Chapter-Batches**.

---

## 5. Novel Vector (The "Secret Sauce")

**"Latent Emotion Shifting"**: Unlike standard readers, our system won't just use a "Happy" or "Sad" voice. We will explore using the LLM to provide a **"Prompt-Based Style."**

- *Example*: If the text says *"He spoke with a mouth full of food,"* we will attempt to pass a "muffled" style descriptor to the TTS engine.

---

## 6. Critical Path: Immediate Next Steps

1. **Environment Setup**: Create a dedicated Conda environment.
2. **Extraction Script**: Build the Python logic to turn an Ebook into a clean text stream.
3. **The "Director" Prompt**: Craft the system prompt for Llama 3.2 that reliably turns text into our structured `script.json`.

---

**Next Session Goal**: We will begin with **Stage 1: The Scripter**. We will focus on getting your laptop to identify characters and dialogue accurately using Llama 3.2.