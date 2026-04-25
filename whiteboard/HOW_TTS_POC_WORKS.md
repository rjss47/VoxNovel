# How `tts_poc.py` Works — A Complete Walkthrough

This document breaks down every piece of `tts_poc.py` so you can understand exactly what each line does, **why** it does it, and what concepts are at play. Think of it as a guided tour of the script, from imports to output.

---

## Table of Contents

1. [The Big Picture](#1-the-big-picture)
2. [Imports — What Libraries Do We Need?](#2-imports--what-libraries-do-we-need)
3. [Parsing the Dialogue File](#3-parsing-the-dialogue-file)
4. [The Main Function](#4-the-main-function)
5. [Loading the TTS Model](#5-loading-the-tts-model)
6. [Mapping Characters to Voices](#6-mapping-characters-to-voices)
7. [The Synthesis Loop](#7-the-synthesis-loop)
8. [Stitching Audio Together & Saving](#8-stitching-audio-together--saving)
9. [The `if __name__` Guard](#9-the-if-__name__-guard)
10. [Key Concepts Glossary](#10-key-concepts-glossary)

---

## 1. The Big Picture

Here's what the script does at 30,000 feet:

```
sample.txt  ──►  Parse lines  ──►  Generate speech per line  ──►  Stitch together  ──►  final_dialogue.wav
```

1. **Read** a text file (`sample.txt`) where each line is formatted as `Speaker: Dialogue`.
2. **Convert** each line of dialogue into audio using a local, offline TTS engine called **Kokoro-ONNX**.
3. **Assign** a distinct synthetic voice to each character.
4. **Concatenate** all the audio clips (with small pauses between them) into one `.wav` file.

No internet connection is needed — everything runs locally on your machine.

---

## 2. Imports — What Libraries Do We Need?

```python
import numpy as np          # 1
import soundfile as sf       # 2
from kokoro_onnx import Kokoro  # 3
import re                   # 4
```

### Line-by-line:

| # | Import | What it is | Why we need it |
|---|--------|-----------|----------------|
| 1 | `numpy` (aliased as `np`) | The fundamental Python library for working with arrays of numbers. | Audio is just a long array of floating-point numbers (samples). NumPy lets us create silence arrays and concatenate audio clips together. |
| 2 | `soundfile` (aliased as `sf`) | A library for reading and writing audio files (WAV, FLAC, OGG, etc.). | We use `sf.write()` at the very end to save our final audio array to a `.wav` file. |
| 3 | `Kokoro` from `kokoro_onnx` | The TTS (Text-to-Speech) engine. It uses ONNX Runtime under the hood to run a neural network that converts text into speech audio. | This is the core of the whole script — it turns text strings into numpy arrays of audio samples. |
| 4 | `re` | Python's built-in **regular expressions** module. | We use it to split each line of dialogue into a `speaker` name and the `text` they say. |

### What is ONNX?

ONNX stands for **Open Neural Network Exchange**. It's a universal format for machine learning models. Instead of needing PyTorch or TensorFlow installed (which are huge), you can export a trained model to `.onnx` format and run it with the much lighter **ONNX Runtime**. That's why this script can run locally without a GPU or heavy ML frameworks.

---

## 3. Parsing the Dialogue File

```python
def parse_dialogue(filepath):
    """Parses the sample.txt file and returns a list of (speaker, text) tuples."""
    dialogue = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Match "Speaker: Text" pattern
            match = re.match(r'^([^:]+):\s*(.*)$', line)
            if match:
                speaker = match.group(1).strip()
                text = match.group(2).strip()
                dialogue.append((speaker, text))
    return dialogue
```

### What this function does:

It reads a text file and turns it into **structured data** — a list of tuples like:

```python
[
    ("Sarah", "Elias? Are you actually up here? ..."),
    ("Elias", "Careful where you step, Sarah. ..."),
    # ...
]
```

### Step-by-step breakdown:

1. **`dialogue = []`** — Start with an empty list to collect results.

2. **`with open(filepath, 'r', encoding='utf-8') as f:`** — Open the file for reading.
   - `'r'` = read mode.
   - `encoding='utf-8'` = handle special characters properly (accents, emojis, etc.).
   - The `with` statement ensures the file is automatically closed when we're done, even if an error occurs.

3. **`for line in f:`** — Loop through the file one line at a time.

4. **`line = line.strip()`** — Remove any leading/trailing whitespace and newline characters (`\n`, `\r`).

5. **`if not line: continue`** — If the line is empty (blank line between dialogue entries), skip it.

6. **The regex**: `r'^([^:]+):\s*(.*)$'` — This is where the magic parsing happens.

### Breaking down the regex:

```
^          Start of the line
([^:]+)    CAPTURE GROUP 1: One or more characters that are NOT a colon
                            → this captures the speaker name (e.g., "Sarah")
:          A literal colon character
\s*        Zero or more whitespace characters (space after the colon)
(.*)       CAPTURE GROUP 2: Everything else until end of line
                            → this captures the dialogue text
$          End of the line
```

So for the line `Sarah: Hello there!`:
- `match.group(1)` → `"Sarah"`
- `match.group(2)` → `"Hello there!"`

7. **`.strip()`** on both groups removes any extra spaces.

8. **`dialogue.append((speaker, text))`** — Add the tuple to our list.

### What's a tuple?

A **tuple** is like a list, but immutable (you can't change it after creation). We write it with parentheses: `("Sarah", "Hello")`. Here it's a natural fit because each dialogue entry has exactly two fixed parts: a speaker and their text.

---

## 4. The Main Function

```python
def main():
    print("Starting TTS POC (ONNX Engine)...")
    print("1. Loading Kokoro ONNX Pipeline...")
```

We wrap everything in a `main()` function rather than putting code at the top level. This is a common Python pattern — it keeps the code organized and makes it importable by other scripts without accidentally running.

The `print()` statements act as progress indicators since TTS generation can take time.

---

## 5. Loading the TTS Model

```python
    kokoro = Kokoro("kokoro-v0_19.onnx", "voices.bin")
```

This single line does a lot under the hood:

1. **Loads the ONNX model** (`kokoro-v0_19.onnx`) — this is a ~80MB neural network that has been trained on thousands of hours of speech to learn how to turn text into realistic-sounding audio waveforms.

2. **Loads the voice embeddings** (`voices.bin`) — this is a binary file containing **voice vectors**. Each named voice (like `am_adam`, `af_bella`) is stored as a vector of numbers that tells the model *how* to sound — pitch, tone, speaking style, etc.

### Where do these files come from?

When you installed `kokoro-onnx` via pip, it gave you the Python wrapper. But the actual model files (`kokoro-v0_19.onnx` and `voices.bin`) need to be present in the working directory (or you pass the full path). These were likely downloaded from the Kokoro project's releases.

---

## 6. Mapping Characters to Voices

```python
    voice_map = {
        'Elias': 'am_adam',   # American Male
        'Sarah': 'af_bella'   # American Female
    }
```

This is a Python **dictionary** — a key-value lookup table. It maps character names (as they appear in `sample.txt`) to Kokoro voice IDs.

### Voice ID naming convention:

Kokoro voice IDs follow a pattern:

```
af_bella
││  └── voice name
│└───── gender: f = female, m = male
└────── accent/language: a = American, b = British, etc.
```

So:
- `am_adam` = **A**merican **M**ale voice named "adam"
- `af_bella` = **A**merican **F**emale voice named "bella"

### Fallback voice:

Later in the code, if a speaker name isn't found in this map:

```python
voice = voice_map.get(speaker, 'af_heart')  # fallback voice
```

`.get(key, default)` returns the value for `key` if it exists, otherwise returns `default`. So any unexpected speaker gets the `af_heart` voice instead of crashing with a `KeyError`.

---

## 7. The Synthesis Loop

```python
    all_audio_segments = []
    sample_rate = 24000  # default fallback

    for i, (speaker, text) in enumerate(dialogue_lines):
        voice = voice_map.get(speaker, 'af_heart')
        print(f"  [{i+1}/{len(dialogue_lines)}] Generating {speaker} using {voice}...")

        samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
        sample_rate = sr

        all_audio_segments.append(samples)

        silence = np.zeros(int(sample_rate * 0.25), dtype=np.float32)
        all_audio_segments.append(silence)
```

This is the heart of the script. Let's unpack each part:

### `enumerate(dialogue_lines)`

`enumerate()` gives you both the **index** (`i`) and the **value** from a list. So instead of manually tracking `i = 0; i += 1`, you get it for free:

```python
# Without enumerate:
i = 0
for item in my_list:
    print(i, item)
    i += 1

# With enumerate (cleaner):
for i, item in enumerate(my_list):
    print(i, item)
```

### Tuple unpacking: `(speaker, text)`

Since each item in `dialogue_lines` is a tuple like `("Sarah", "Hello")`, we can unpack it directly in the loop header:

```python
for i, (speaker, text) in enumerate(dialogue_lines):
    # speaker = "Sarah"
    # text = "Hello"
```

### `kokoro.create()` — The actual TTS call

```python
samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
```

This is where text becomes audio. The method returns **two values**:

| Return value | What it is |
|-------------|-----------|
| `samples` | A **NumPy array** of floating-point numbers, typically between -1.0 and 1.0. Each number is one audio **sample** — a snapshot of the sound wave at a point in time. |
| `sr` | The **sample rate** — how many samples represent one second of audio. Here it's 24,000, meaning 24,000 numbers = 1 second of audio. |

**Parameters:**
- `text` — The string to speak.
- `voice=voice` — Which voice embedding to use.
- `speed=1.0` — Normal speed. `0.5` = half speed, `2.0` = double speed.
- `lang="en-us"` — Language/accent hint for pronunciation.

### Adding silence between lines

```python
silence = np.zeros(int(sample_rate * 0.25), dtype=np.float32)
all_audio_segments.append(silence)
```

This creates a **quarter-second pause** between dialogue lines. Here's why:

- `sample_rate * 0.25` = `24000 * 0.25` = `6000` samples
- `np.zeros(6000, dtype=np.float32)` creates an array of 6,000 zeros
- In audio, a zero value = silence (no sound wave displacement)
- `dtype=np.float32` ensures the silence array matches the format of the speech audio

Without these pauses, one character's speech would immediately slam into the next, sounding unnatural.

### What is a sample rate?

Think of audio like a flipbook animation. Each "page" is a **sample** — a single measurement of the sound wave's position. The **sample rate** is how many pages you flip per second:

- **24,000 Hz** (this script) = 24,000 measurements per second — good quality for speech
- **44,100 Hz** = CD quality
- **48,000 Hz** = professional audio / video standard

Higher sample rate = more detail = larger files.

---

## 8. Stitching Audio Together & Saving

```python
    final_audio = np.concatenate(all_audio_segments)
    sf.write("final_dialogue.wav", final_audio, sample_rate)
```

### `np.concatenate()`

Takes a list of arrays and joins them end-to-end into one long array:

```
[Sarah_audio] + [silence] + [Elias_audio] + [silence] + ... = [final_audio]
```

If Sarah's line produces 48,000 samples (2 seconds) and Elias's produces 72,000 samples (3 seconds), plus silences, they all get glued together in order.

### `sf.write()`

Writes the final numpy array to disk as a `.wav` file:

- `"final_dialogue.wav"` — output filename
- `final_audio` — the audio data (numpy array)
- `sample_rate` — tells the WAV file header "this audio should be played back at 24,000 samples per second"

### What is a WAV file?

WAV is an **uncompressed** audio format. It stores the raw samples directly (unlike MP3 which compresses them). This means:
- ✅ No quality loss
- ✅ Simple to create — just dump the array with a header
- ❌ Large file sizes (~2.6 MB per minute at 24kHz mono)

For a POC, WAV is perfect because it avoids the complexity of encoding.

---

## 9. The `if __name__` Guard

```python
if __name__ == "__main__":
    main()
```

This is a Python idiom you'll see everywhere. Here's what it means:

- Every Python file has a special variable called `__name__`.
- When you **run the file directly** (`python tts_poc.py`), Python sets `__name__` to `"__main__"`.
- When you **import the file** from another script (`from tts_poc import parse_dialogue`), `__name__` is set to `"tts_poc"` instead.

So this guard says: "Only run `main()` if this script is being executed directly, not imported." This lets other scripts reuse `parse_dialogue()` without triggering the entire TTS pipeline.

---

## 10. Key Concepts Glossary

| Term | Meaning |
|------|---------|
| **TTS** | Text-to-Speech — converting written text into spoken audio. |
| **ONNX** | Open Neural Network Exchange — a portable format for ML models that can run without PyTorch/TensorFlow. |
| **ONNX Runtime** | A lightweight engine that executes ONNX models. Used internally by `kokoro_onnx`. |
| **Sample** | A single numerical measurement of a sound wave at one point in time. |
| **Sample Rate (Hz)** | How many samples represent one second of audio. 24,000 Hz = 24,000 samples/sec. |
| **NumPy Array** | A highly efficient, fixed-type array. Audio samples are stored as `float32` arrays. |
| **Voice Embedding** | A vector of numbers that encodes the characteristics of a voice (pitch, tone, style). Stored in `voices.bin`. |
| **Regex** | Regular Expression — a pattern-matching language for text. Used here to split `"Speaker: Text"` lines. |
| **WAV** | An uncompressed audio file format. Simple and lossless. |
| **Tuple** | An immutable ordered collection in Python, written with parentheses: `(a, b)`. |
| **Dictionary** | A key→value lookup table in Python, written with braces: `{"key": "value"}`. |
| **POC** | Proof of Concept — a minimal prototype to validate an idea works. |

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          tts_poc.py                                     │
│                                                                         │
│  ┌──────────┐     ┌────────────────┐     ┌─────────────────────────┐   │
│  │sample.txt│────►│parse_dialogue()│────►│List of (speaker, text)  │   │
│  │          │     │  (regex split) │     │tuples                   │   │
│  └──────────┘     └────────────────┘     └───────────┬─────────────┘   │
│                                                       │                 │
│  ┌──────────────────────┐                            ▼                 │
│  │kokoro-v0_19.onnx     │     ┌──────────────────────────────────┐     │
│  │   (neural network)   │────►│  kokoro.create(text, voice=...)  │◄──┐│
│  │voices.bin            │     │  → returns (samples, rate)       │   ││
│  │   (voice embeddings) │     └──────────┬───────────────────────┘   ││
│  └──────────────────────┘                │                           ││
│                                          ▼                           ││
│  ┌─────────────┐    ┌────────────────────────────────────┐          ││
│  │ voice_map   │───►│  Loop: for each dialogue line      │──────────┘│
│  │ dict lookup │    │    → pick voice                    │           │
│  └─────────────┘    │    → generate audio                │           │
│                     │    → append silence gap (0.25s)    │           │
│                     └──────────────┬─────────────────────┘           │
│                                    │                                 │
│                                    ▼                                 │
│                     ┌──────────────────────────────────┐             │
│                     │  np.concatenate(all_segments)    │             │
│                     │  sf.write("final_dialogue.wav")  │             │
│                     └──────────────┬───────────────────┘             │
│                                    │                                 │
└────────────────────────────────────┼─────────────────────────────────┘
                                     ▼
                            ┌─────────────────┐
                            │final_dialogue.wav│
                            │ (playable audio) │
                            └─────────────────┘
```

---

## Quick Experiments You Can Try

Now that you understand the code, here are some things to tweak and learn from:

1. **Change the pause duration** — Edit `0.25` to `0.75` and hear how the pacing changes.
2. **Swap voices** — Try `bf_emma` (British Female) or `bm_george` (British Male) in the voice map.
3. **Adjust speed** — Change `speed=1.0` to `speed=0.8` for slower, more dramatic reading.
4. **Add a narrator** — Add a `Narrator` key to `voice_map` and add narrator lines to `sample.txt`.
5. **Print the raw data** — Add `print(samples.shape, samples.dtype)` after `kokoro.create()` to see the actual array dimensions and data type.

---

*This document was written as a learning companion for the VoxNovel TTS proof-of-concept.*
