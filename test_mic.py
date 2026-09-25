#!/usr/bin/env python3
"""Test microphone recording and transcription."""
import sys
sys.path.insert(0, '.')
import tempfile
import subprocess
from pathlib import Path
import speech_recognition as sr

print("=" * 50)
print("  MICROPHONE TEST")
print("=" * 50)
print()

print("Step 1: Checking microphone...")
result = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
if "card 0" in result.stdout or "card 1" in result.stdout:
    print("  ✓ Microphone detected")
else:
    print("  ✗ No microphone found")
    sys.exit(1)

print()
print("Step 2: Recording 5 seconds of audio...")
print("  *** SPEAK CLEARLY INTO YOUR MICROPHONE NOW ***")
print()

temp_path = tempfile.mktemp(suffix=".wav")
proc = subprocess.Popen(
    ["arecord", "-f", "S16_LE", "-r", "16000", "-c", "1", "-d", "5", temp_path],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
stdout, stderr = proc.communicate(timeout=10)

if not Path(temp_path).exists() or Path(temp_path).stat().st_size < 1000:
    print("  ✗ Recording failed")
    sys.exit(1)

print("  ✓ Recording complete")

print()
print("Step 3: Checking audio levels...")

import wave
import struct

with wave.open(temp_path, 'rb') as wf:
    frames = wf.readframes(wf.getnframes())
    samples = struct.unpack(f'<{len(frames)//2}h', frames)
    max_val = max(abs(s) for s in samples)
    avg_val = sum(abs(s) for s in samples) / len(samples)
    
    print(f"  Max volume: {max_val}")
    print(f"  Avg volume: {avg_val:.0f}")
    
    if max_val < 100:
        print("  ✗ Audio too quiet - speak louder!")
    elif max_val < 1000:
        print("  ⚠ Audio quiet - try speaking closer to mic")
    else:
        print("  ✓ Good audio levels")

print()
print("Step 4: Transcribing with Google...")

recognizer = sr.Recognizer()
with sr.AudioFile(temp_path) as source:
    audio = recognizer.record(source)

try:
    text = recognizer.recognize_google(audio)
    print(f"  ✓ Transcribed: \"{text}\"")
    print()
    print("SUCCESS! Your microphone is working!")
except sr.UnknownValueError:
    print("  ✗ Could not understand - try speaking louder/clearer")
except sr.RequestError as e:
    print(f"  ✗ API error: {e}")

try:
    Path(temp_path).unlink()
except Exception:
    pass

print()
print("=" * 50)
