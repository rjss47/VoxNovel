import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
import re

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

def main():
    print("Starting TTS POC (ONNX Engine)...")
    print("1. Loading Kokoro ONNX Pipeline...")
    
    # Load the ONNX model and voices file
    kokoro = Kokoro("kokoro-v0_19.onnx", "voices.bin")

    print("2. Parsing dialogue from sample.txt")
    dialogue_lines = parse_dialogue('sample.txt')
    
    if not dialogue_lines:
        print("No dialogue found in sample.txt! Check the file format.")
        return

    # To store all the generated audio segments
    all_audio_segments = []
    
    # Voice mapping
    voice_map = {
        'Elias': 'am_adam',   # American Male
        'Sarah': 'af_bella'   # American Female
    }

    print(f"3. Generating audio for {len(dialogue_lines)} lines...")
    sample_rate = 24000 # default fallback
    for i, (speaker, text) in enumerate(dialogue_lines):
        voice = voice_map.get(speaker, 'af_heart') # fallback voice
        print(f"  [{i+1}/{len(dialogue_lines)}] Generating {speaker} using {voice}...")
        
        # kokoro.create returns the audio array and the sample rate
        samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
        sample_rate = sr
        
        all_audio_segments.append(samples)
        
        # Add a 0.25 second pause after the speaker finishes their line
        silence = np.zeros(int(sample_rate * 0.25), dtype=np.float32)
        all_audio_segments.append(silence)

    print("4. Concatenating audio and saving to final_dialogue.wav")
    final_audio = np.concatenate(all_audio_segments)
    
    sf.write("final_dialogue.wav", final_audio, sample_rate)
    print("Done! You can now listen to final_dialogue.wav")

if __name__ == "__main__":
    main()
