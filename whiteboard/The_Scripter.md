# Stage 1: The Scripter

**Objective**: Turn a raw novel text file into a structured `script.json` that a TTS pipeline can consume.

**Test Material**: "A Scandal in Bohemia" by Arthur Conan Doyle (3 parts, ~8,500 words)

---

## Stage 1 Goals

1. **Clean Ingestion**: Read the raw text, clean it, and chunk it intelligently.
2. **Cast Discovery**: Generate a deduplicated list of all characters.
3. **Dialogue Extraction**: Isolate every piece of spoken text.
4. **Attribution**: Link every piece of dialogue to a specific character (or "Narrator").
5. **Emotional Tagging**: Assign a tone to each line from: `neutral`, `happy`, `sad`, `angry`, `whispering`, `excited`, `sarcastic`.

---

## Step 1: Setup the Local "Brain"

- **Action**: Install **Ollama** (see `ollama_setup.md` for the full guide).
- **Command**: `ollama pull llama3.2:3b`
- **Why 3B over 1B**: The 3B model is much better at instruction-following and logical reasoning. It fits easily in your 4GB dedicated VRAM (~2GB quantized).
- **Verify**: Run `ollama run llama3.2:3b` and send a simple prompt to confirm it responds.

---

## Step 2: The Text Chunker (`ingest.py`)

### Concept
You cannot feed a whole book to the LLM at once — it will lose focus and accuracy degrades with very long inputs. We break the text into digestible chunks.

### Requirements
- Read a `.txt` file and break it into chunks of roughly **1,000–1,500 words**.
- **Break at natural boundaries**: paragraphs (`\n\n`), scene breaks (`***`, `---`, or extra whitespace), and chapter markers.
- **Never break mid-sentence**. If a chunk boundary falls inside a sentence, extend the chunk to the next sentence end.

### ⚠️ Sliding Window Overlap (CRITICAL)
If a dialogue starts at the end of Chunk 1 and its attribution ("said Holmes") is at the start of Chunk 2, the LLM will miss it. To fix this:

- Each chunk should include the **last ~200 words of the previous chunk** as overlap.
- When merging results, discard the overlapping region's output from the second chunk (keep the first chunk's version — it had more context).

### Output
A list of text chunks stored in memory (or a temp JSON file), ready to be sent to the LLM.

```
Raw text → [Chunk 1 (1200 words)] [Chunk 2 (200 overlap + 1000 new)] [Chunk 3 ...] → ...
```

---

## Step 3: The Cast List Pre-Pass (`discover_characters.py`)

### Concept
The LLM performs much better at attribution if it knows the "Cast of Characters" before it starts. Instead of scanning only the first few chunks, we scan **ALL chunks** for a comprehensive cast.

### Process
1. Send **every chunk** to the LLM with a simple prompt:
   > "List all character names mentioned in this text. Output ONLY a JSON array of strings. Example: ["Holmes", "Watson"]"

2. Use Ollama's `format: "json"` parameter to force clean JSON output.

3. **Deduplicate and normalize** across all chunks:
   - "Sherlock Holmes", "Holmes", "Sherlock" → all map to `"Holmes"`
   - "the King", "King of Bohemia", "Wilhelm Gottsreich Sigismond von Ormstein" → all map to `"King of Bohemia"`
   - Ask the LLM to help with this: send the raw list and ask it to merge duplicates.

4. Always include `"Narrator"` in the final list — the narrator speaks all non-dialogue text.

### Output
`characters.json` — a clean list of unique character identifiers.

```json
{
  "characters": ["Holmes", "Watson", "King of Bohemia", "Irene Adler", "Godfrey Norton", "Narrator"],
  "aliases": {
    "Holmes": ["Sherlock Holmes", "Sherlock", "Holmes"],
    "Watson": ["Dr. Watson", "Watson", "Doctor", "John"],
    "King of Bohemia": ["the King", "Count Von Kramm", "Wilhelm Gottsreich Sigismond von Ormstein", "His Majesty"]
  }
}
```

---

## Step 4: The Attribution Prompt (`attribute.py`) — THE CORE

### Concept
This is where you send each text chunk + the cast list to the LLM, and it returns structured JSON with speaker, text, and emotion for every line.

### The Prompt Strategy

**System Prompt:**
```
You are a professional scriptwriter analyzing a novel. You will receive a cast list and a passage of text. Your job is to convert the passage into a JSON array where each element represents one continuous segment of text.

Rules:
1. Every piece of text must be attributed — nothing is skipped.
2. Quoted dialogue is attributed to the character who speaks it.
3. All non-dialogue text (descriptions, narration, actions) is attributed to "Narrator".
4. Each entry must have: "speaker", "text", and "tone".
5. Tone must be one of: neutral, happy, sad, angry, whispering, excited, sarcastic.
6. Preserve the EXACT original text — do not summarize or paraphrase.
7. Output ONLY valid JSON. No commentary, no markdown.
```

**User Prompt (per chunk):**
```
Cast: [Holmes, Watson, King of Bohemia, Irene Adler, Narrator]

Previous context (last 3 lines):
- Watson (neutral): "I can't imagine. I suppose that you have been watching..."
- Holmes (excited): "Quite so; but the sequel was rather unusual..."
- Narrator (neutral): He disappeared into his bedroom and returned...

Now convert the following passage:
[CHUNK TEXT HERE]
```

### Expected Output
```json
[
  {"speaker": "Narrator", "text": "His manner was not effusive. It seldom was; but he was glad, I think, to see me.", "tone": "neutral"},
  {"speaker": "Holmes", "text": "Wedlock suits you. I think, Watson, that you have put on seven and a half pounds since I saw you.", "tone": "sarcastic"},
  {"speaker": "Watson", "text": "Seven!", "tone": "surprised"}
]
```

### ⚠️ Context Carryover (CRITICAL)
Each chunk prompt must include the **last 2-3 attributed lines** from the previous chunk's output. This gives the LLM continuity so it knows:
- Who was speaking last
- What the conversation flow is
- How to resolve "he said" / "she replied" when the referent is in the previous chunk

### JSON Enforcement
- Use Ollama's API with `format: "json"` to force JSON-only output.
- As a safety net, also use a regex to extract content between `[` and `]` in case the model wraps it.
- Validate each response: check that every entry has all 3 fields, that speakers are from the cast list, and that tones are from the allowed set.

---

## Step 5: The Glue Script (`scripter.py`)

### Action
Create the main orchestrator that ties Steps 2–4 together:

1. **Ingest** the text file → get chunks (Step 2)
2. **Discover** characters across all chunks → get cast list (Step 3)
3. **Attribute** each chunk sequentially → accumulate results (Step 4)
   - Pass previous context to each chunk
   - Handle the overlap: discard duplicate entries from overlapping regions
4. **Merge** all results into a single `script.json`
5. **Validate** the final output (Step 6)

### Output: `script.json`
```json
{
  "metadata": {
    "title": "A Scandal in Bohemia",
    "author": "Arthur Conan Doyle",
    "total_lines": 247,
    "characters_found": 6,
    "processed_at": "2026-04-26T02:00:00"
  },
  "characters": ["Holmes", "Watson", "King of Bohemia", "Irene Adler", "Godfrey Norton", "Narrator"],
  "script": [
    {"line_id": 1, "speaker": "Narrator", "text": "To Sherlock Holmes she is always the woman...", "tone": "neutral"},
    {"line_id": 2, "speaker": "Holmes", "text": "Wedlock suits you...", "tone": "sarcastic"},
    ...
  ]
}
```

---

## Step 6: Validation (`validate_script.py`)

### Checks to Run
1. **Unknown speakers**: Flag any speaker not in the cast list (likely an LLM hallucination).
2. **One-hit wonders**: Characters that appear only once are suspicious — probably an alias or hallucination.
3. **Empty text**: Any entries with blank or very short text.
4. **Tone distribution**: Print a summary — if 95% is "neutral", the emotion tagging isn't working.
5. **Coverage**: Compare total character count of `script.json` text vs. original file — they should be close (no text lost).

### Output
Print a summary report to the console:
```
=== Script Validation Report ===
Total lines: 247
Characters: Holmes(45), Watson(38), King(22), Narrator(130), Irene(8), Norton(4)
Tones: neutral(150), sarcastic(22), excited(18), sad(5), ...
Coverage: 98.3% of original text preserved
Warnings: 0 unknown speakers, 0 empty entries
✅ Script looks good!
```

---

## Potential Bottlenecks

| Issue | Mitigation |
|---|---|
| **JSON hallucinations** — LLM adds "Sure, here is your JSON" | Use `format: "json"` in Ollama API + regex extraction fallback |
| **"Who is He?"** — pronoun resolution fails | Context carryover (last 2-3 lines) + cast list in every prompt |
| **Character name inconsistency** — "Holmes" vs "Sherlock" | Dedicated deduplication step in character discovery |
| **Overlapping chunks produce duplicate lines** | Track overlap boundaries, discard duplicates from second chunk |
| **LLM speed** — Llama 3.2 3B on 4GB VRAM | ~1-2 min per chunk is normal. A 3-chapter story should take ~15-20 min total |
| **Thermal throttling** — laptop heats up on sustained LLM use | Process in batches, add 5-second cooldown between chunks if needed |

---

## Success Criteria

**Goal**: Get "A Scandal in Bohemia" (all 3 parts) successfully converted into a `script.json`.

**When we review, we check:**
1. Did Llama 3.2 3B accurately identify the speakers? (Target: >90% accuracy)
2. How long did it take to process the full story?
3. Did the JSON format stay consistent across all chunks?
4. Are the emotion tags reasonable? (Holmes should be sarcastic sometimes, the King should be agitated, etc.)

---

*Once we have a clean `script.json`, Stage 2 (The Casting Director) becomes straightforward — it just reads the character list and assigns voices. Focus entirely on the accuracy of this data.*