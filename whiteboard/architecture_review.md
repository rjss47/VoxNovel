# VoxNovel — Architecture Review & Game Plan

## 0. Hardware Profile

| Spec | Value |
|---|---|
| **Machine** | Dell G15 5525 |
| **CPU** | AMD Ryzen 5 6600H (3.30 GHz, 6C/12T) |
| **RAM** | 16 GB (15.2 GB usable) |
| **GPU** | NVIDIA RTX 3050 Laptop — **4GB dedicated VRAM + 7.6GB shared** (11.6GB total) |
| **iGPU** | AMD Radeon (integrated, not used for ML) |
| **Storage** | NVMe SSD |
| **OS** | Windows 11 Home 25H2 |

> 💡 The 7.6GB shared GPU memory uses system RAM as overflow — slower than dedicated VRAM but prevents OOM crashes. This means Ollama with Llama 3.2 3B will comfortably fit (the quantized model is ~2GB, well within 4GB dedicated).

---

## 1. Verdict: Is the README Approach Sound?

**Yes — the 4-stage sequential pipeline is an excellent architecture.** The core idea of stage-gating (only one heavy model in VRAM at a time) is the right strategy. The pipeline stages are cleanly separated with well-defined inputs/outputs, which means you can build, test, and iterate on each stage independently.

However, several **specific technology choices are outdated or problematic** and need to be updated. The *architecture* is great; the *component selection* needs a refresh. Details below.

---

## 2. Technology Audit — What Needs to Change

### ✅ What's Still Good

| Component | Original Choice | Status |
|---|---|---|
| **Orchestration** | Python 3.10+ | ✅ You're on 3.11. |
| **LLM (Director)** | Llama 3.2 3B via Ollama | ✅ 128k context, ~2GB quantized, fits in 4GB VRAM easily. |
| **Audio Engine** | FFmpeg / Pydub | ✅ FFmpeg is the gold standard. |
| **Data Storage** | JSON files | ✅ Fine for a local prototype. |

### ❌ What Needs to Change

| Component | Original Choice | Problem | Replacement |
|---|---|---|---|
| **TTS Engine** | XTTSv2 (Coqui) | **Coqui AI shut down in 2024.** Unmaintained, painful to install, needs ~6GB VRAM. | **Kokoro ONNX** (already proven in POC!) |
| **Emotion Approach** | "Latent Emotion Shifting" via reference audio | Dies with XTTSv2. Kokoro has no native emotion tags. | **Prosody hinting** via speed/pause/punctuation |

> ⚠️ **XTTSv2 is dead.** Coqui AI closed. Community forks exist but are fragile. Don't build on it.

> ℹ️ **Chatterbox TTS** (Resemble AI) has real emotion control, but needs ~6-7GB VRAM. Won't fit dedicated VRAM, and running in shared memory would be painfully slow for generating hundreds of clips. Keep it on the radar for a future v2. **Kokoro is the right call for v1.**

### Finalized Stack (v1)

| Component | Technology | Why |
|---|---|---|
| **Orchestration** | Python 3.11 + `uv` | Already set up. |
| **LLM (Director)** | Llama 3.2 3B (Q4_K_M) via Ollama | Attribution, character discovery, emotion tagging. ~2GB VRAM. |
| **TTS (Actor)** | Kokoro ONNX | Proven in POC. 82M params, runs on CPU, high quality. |
| **Audio Engine** | `numpy` + `soundfile` + FFmpeg | Numpy for stitching, FFmpeg for MP3 conversion. |
| **Text Extraction** | Manual `.txt` for v1, `ebooklib` later | Start simple. |
| **Data Format** | JSON | `script.json`, `character_map.json`, `sync_map.json` |

---

## 3. The Emotion Control Problem (v1 Approach)

Kokoro ONNX has no emotion tags. Here's what we CAN do:

1. **Speed modulation** — Slow for sad/dramatic (0.85x), fast for excited (1.1x)
2. **Pause engineering** — Longer pauses before dramatic lines, shorter for rapid dialogue
3. **Punctuation cues** — Ellipses for hesitation, exclamation for emphasis — Kokoro responds to these naturally
4. **Voice variety** — Different Kokoro voice IDs have inherently different tones (warmer, gruffer, etc.)

This won't give us "muffled" or "whispering" but it'll make the output sound much more alive than flat TTS. Good enough for a v1 prototype.

**Emotion tags we'll use** (from LLM tagging):
`neutral`, `happy`, `sad`, `angry`, `whispering`, `excited`, `sarcastic`

These will map to speed/pause adjustments in the synthesis stage.

---

## 4. Review of The_Scripter.md

The plan is **directionally correct** with these refinements needed:

| Step | Status | Note |
|---|---|---|
| 1. Ollama setup | ✅ Good | 3B is the right call. |
| 2. Text chunker | ⚠️ Needs work | Add sliding window overlap (~200 words) so cross-chunk dialogues aren't lost. Break at scene breaks too. |
| 3. Cast list pre-pass | ⚠️ Enhance | Scan ALL chunks, not just first 2-3. Full-text character sweep. |
| 4. Attribution prompt | ⚠️ Needs work | Add context carryover (last 2-3 lines from previous chunk). Use Ollama `format: "json"`. |
| 5. Glue script | ✅ Good | Just add overlap + carryover. |

**Additional needs not in the original plan:**
- Character name normalization ("Holmes", "Sherlock", "he" → same entity)
- Validation pass to catch hallucinated speakers
- Narrator text handling (descriptions, scene-setting between dialogue)

---

## 5. The Game Plan — Learning Phases

> **Philosophy**: Each phase is both a learning milestone AND an engineering milestone. Build, understand, then move on. No rushing.

### Phase 0: Foundation ✅
- [x] TTS POC with Kokoro ONNX
- [x] Understand how TTS works (HOW_TTS_POC_WORKS.md)
- [ ] Install Ollama + pull `llama3.2:3b`
- [ ] Prepare test text (3 chapters of Sherlock Holmes from Project Gutenberg)

### Phase 1: The Scripter
**Goal**: Turn raw novel text → structured `script.json`
**You'll learn**: LLM prompting, JSON parsing, text chunking, NLP basics

| Sub-step | Script | What it does |
|---|---|---|
| 1A | `ingest.py` | Read `.txt`, clean it, chunk it with overlap |
| 1B | `discover_characters.py` | LLM first-pass: find all characters |
| 1C | `attribute.py` | LLM second-pass: speaker + emotion per line |
| 1D | `validate_script.py` | Sanity check the output |

**Milestone**: 3 chapters of Sherlock Holmes → clean `script.json` with accurate speaker attribution.

### Phase 2: The Casting Director
**Goal**: Auto-assign voices to characters
**You'll learn**: Data analysis, configuration design

**Milestone**: `character_map.json` auto-generated from `script.json`.

### Phase 3: The Recording Studio
**Goal**: Generate audio for every line
**You'll learn**: Audio generation at scale, performance optimization

**Milestone**: Hundreds of `.wav` files with correct voices + `sync_map.json`.

### Phase 4: The Sound Engineer
**Goal**: Stitch into final chapter audio files
**You'll learn**: Audio processing, FFmpeg, volume normalization

**Milestone**: 3 polished `.mp3` files (one per chapter) — shareable with friends.

### Phase 5 (Future): Polish
- EPUB support
- CLI runner (`python voxnovel.py book.epub`)
- Batch processing improvements
- Potential TTS engine upgrade (Chatterbox when hardware allows)

---

## 6. Test Material: Sherlock Holmes

**Source**: "The Adventures of Sherlock Holmes" by Arthur Conan Doyle — Project Gutenberg (100% public domain).

**Why it's perfect**:
- Multiple characters per story (Holmes, Watson, clients, villains)
- Mix of dialogue and narrative description
- Clear "said" attributions (good for validation)
- Some tricky implicit attributions (good for testing LLM capability)
- Emotional range (mystery, tension, humor, deduction)
- Well-known — easy to verify if the output sounds right

**Suggested 3 chapters**: "A Scandal in Bohemia" (Parts I, II, III) — the first story in the collection. Has Holmes, Watson, the King of Bohemia, and Irene Adler. Good character variety.

---

## 7. Immediate Next Steps

1. ✅ Review this plan
2. **Install Ollama** on Windows
3. **Pull Llama 3.2 3B** — `ollama pull llama3.2:3b`
4. **Download test text** — "A Scandal in Bohemia" from Project Gutenberg
5. **Start Phase 1A** — build the text chunker

---

*Last updated: 2026-04-26 | Hardware: Dell G15 5525, RTX 3050 4GB + 7.6GB shared, 16GB RAM*
