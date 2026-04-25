# Ollama Installation Roadmap (Windows)

A step-by-step guide to get Ollama + Llama 3.2 3B running on your Dell G15 5525.

---

## What is Ollama?

Ollama is a tool that lets you run LLMs (like Llama, Mistral, etc.) locally on your machine. It handles downloading models, managing GPU/CPU offloading, quantization, and provides a simple API. Think of it as "Docker, but for LLMs."

---

## Step 1: Download Ollama

1. Go to **https://ollama.com/download**
2. Click **"Download for Windows"**
3. Run the installer (`OllamaSetup.exe`)
4. Follow the default installation — no special settings needed
5. Ollama installs as a **background service** — it starts automatically with Windows

> 💡 After installation, you'll see a small llama icon in your system tray (bottom-right of taskbar). That means it's running.

---

## Step 2: Verify Installation

Open **PowerShell** (or Windows Terminal) and run:

```powershell
ollama --version
```

You should see something like `ollama version 0.x.x`. If you get "command not found", restart your terminal or reboot.

---

## Step 3: Pull Llama 3.2 3B

This downloads the model (~2GB). Run:

```powershell
ollama pull llama3.2:3b
```

**What happens under the hood:**
- Downloads the 3B parameter model in Q4_K_M quantization (~2GB)
- Stores it in `C:\Users\sreek\.ollama\models\`
- The Q4 quantization means 4-bit precision — fits in your 4GB VRAM with room to spare

Wait for the download to finish. On decent internet, this takes 2-5 minutes.

---

## Step 4: Test It Interactively

Start a chat session:

```powershell
ollama run llama3.2:3b
```

You'll get a `>>>` prompt. Try these tests:

### Test 1: Basic response
```
>>> Who is Sherlock Holmes?
```

### Test 2: JSON output (important for our pipeline)
```
>>> Output ONLY valid JSON. List 3 fictional detectives as a JSON array of objects with "name" and "author" fields.
```

### Test 3: Dialogue attribution (mini version of our task)
```
>>> You are a scriptwriter. Convert this text into a JSON array with "speaker", "text", and "tone" fields. Text: Holmes leaned back in his chair. "Elementary, my dear Watson," he said with a smirk. Watson rolled his eyes. "You always say that."
```

Type `/bye` to exit the interactive session.

---

## Step 5: Verify GPU Usage

While the model is running (during Step 4), open **Task Manager** → **Performance** → **GPU 0 (NVIDIA GeForce RTX 3050)**.

You should see:
- **Dedicated GPU memory** usage jump by ~2GB
- **GPU utilization** spike when generating responses

If the GPU memory doesn't change, Ollama might be running on CPU. This still works but is slower. Check the Troubleshooting section below.

---

## Step 6: Test the API (What Our Python Code Will Use)

Ollama runs a local HTTP API on port **11434**. Our Python scripts will talk to this API. Test it:

```powershell
curl http://localhost:11434/api/generate -d '{\"model\": \"llama3.2:3b\", \"prompt\": \"Say hello in JSON format\", \"stream\": false, \"format\": \"json\"}'
```

If `curl` isn't available, you can test from Python:

```python
import requests
response = requests.post("http://localhost:11434/api/generate", json={
    "model": "llama3.2:3b",
    "prompt": "Say hello in JSON format",
    "stream": False,
    "format": "json"
})
print(response.json()["response"])
```

> 💡 The `"format": "json"` parameter is our secret weapon — it forces the model to output only valid JSON, solving the "JSON hallucination" problem.

---

## Quick Reference

| Item | Value |
|---|---|
| **Ollama download** | https://ollama.com/download |
| **Model** | `llama3.2:3b` (~2GB download) |
| **Model storage** | `C:\Users\sreek\.ollama\models\` |
| **API endpoint** | `http://localhost:11434` |
| **GPU expected** | ~2GB VRAM usage |
| **System tray** | Llama icon = Ollama is running |

---

## Troubleshooting

### "ollama" is not recognized
- Restart your terminal after installation
- If still failing, check if `C:\Users\sreek\AppData\Local\Programs\Ollama` is in your PATH

### Model downloads slowly
- Normal on slow connections — the 3B model is ~2GB
- If it stalls, cancel with `Ctrl+C` and re-run `ollama pull` — it resumes from where it stopped

### GPU not being used (running on CPU)
- Make sure your NVIDIA drivers are up to date (yours: v32.0.15.8195 from Nov 2025 — should be fine)
- Run `ollama ps` while a model is loaded to see where it's running
- If needed: `set OLLAMA_GPU_LAYER=999` before running to force GPU usage

### Out of Memory errors
- Unlikely with the 3B model (only ~2GB VRAM), but if it happens:
  - Close other GPU-using apps (games, Chrome with hardware acceleration, etc.)
  - Try `ollama pull llama3.2:1b` as a lighter alternative (less accurate but uses ~1GB VRAM)

### Laptop getting hot
- This is normal — the GPU is doing real work
- Consider a cooling pad for extended sessions
- We'll add cooldown pauses between chunks in our scripts

---

## After Installation: Next Steps

Once you confirm Ollama + Llama 3.2 3B is working:
1. ✅ You can close the interactive session (`/bye`)
2. ✅ Leave Ollama running in the background (system tray)
3. 🚀 We start building `ingest.py` — the text chunker

---

*This guide is specific to your Dell G15 5525 running Windows 11 25H2 with RTX 3050.*
