"""Advanced TTS Engine with RVC voice conversion."""
import asyncio
import io
import os
import tempfile
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional

# Import edge-tts
try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

# Import RVC converter
try:
    from .rvc_voice import convert_voice, is_available as rvc_available
    HAS_RVC = rvc_available()
except ImportError:
    HAS_RVC = False

# Available edge-tts voices (female voices suitable for Texas Arknights style)
VOICE_OPTIONS = {
    "texas": "en-US-JennyNeural",  # Professional female voice
    "anime": "en-US-AriaNeural",   # Youthful female voice
    "soft": "en-US-SaraNeural",    # Soft female voice
    "default": "en-US-JennyNeural"
}


class TTSEngine:
    """TTS Engine with optional RVC voice conversion."""
    
    def __init__(self, voice: str = "texas", pitch_shift: int = 0):
        """
        Initialize TTS engine.
        
        Args:
            voice: Voice style ("texas", "anime", "soft", "default")
            pitch_shift: Pitch shift for RVC conversion (semitones)
        """
        self.voice = VOICE_OPTIONS.get(voice, VOICE_OPTIONS["default"])
        self.pitch_shift = pitch_shift
        self.use_rvc = HAS_RVC
    
    def speak(self, text: str, output_path: Optional[str] = None) -> dict:
        """
        Convert text to speech.
        
        Args:
            text: Text to speak
            output_path: Optional path to save audio file
            
        Returns:
            dict with success status and audio data
        """
        if not text or not text.strip():
            return {"success": False, "error": "Empty text"}
        
        try:
            # Generate audio with edge-tts
            audio_data = self._generate_edge_tts(text)
            if audio_data is None:
                return {"success": False, "error": "edge-tts generation failed"}
            
            # Apply RVC conversion if available
            if self.use_rvc and audio_data is not None:
                audio_data = self._apply_rvc(audio_data)
            
            # Save to file if requested
            if output_path and audio_data:
                self._save_audio(audio_data, output_path)
            
            # Play audio
            if audio_data:
                self._play_audio(audio_data)
            
            return {
                "success": True,
                "engine": "edge-tts + RVC" if self.use_rvc else "edge-tts",
                "voice": self.voice
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_edge_tts(self, text: str) -> Optional[bytes]:
        """Generate audio using edge-tts."""
        if not HAS_EDGE_TTS:
            return None
        
        try:
            # Create async function for edge-tts
            async def generate():
                communicate = edge_tts.Communicate(text, self.voice)
                audio_data = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                return audio_data
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_data = loop.run_until_complete(generate())
            loop.close()
            
            return audio_data
            
        except Exception as e:
            print(f"edge-tts error: {e}")
            return None
    
    def _apply_rvc(self, audio_data: bytes) -> Optional[bytes]:
        """Apply RVC voice conversion to audio."""
        if not HAS_RVC:
            return audio_data
        
        try:
            # Save temp file for processing
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            # Load audio with torchaudio
            waveform, sr = torchaudio.load(temp_path)
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            
            # Convert to numpy
            audio_np = waveform.squeeze().numpy()
            
            # Apply RVC conversion
            converted = convert_voice(audio_np, sr, self.pitch_shift)
            
            # Convert back to tensor
            converted_tensor = torch.from_numpy(converted).unsqueeze(0)
            
            # Save converted audio
            torchaudio.save(temp_path, converted_tensor, sr)
            
            # Read back
            with open(temp_path, "rb") as f:
                result = f.read()
            
            # Cleanup
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            print(f"RVC conversion failed: {e}")
            return audio_data
    
    def _save_audio(self, audio_data: bytes, path: str):
        """Save audio data to file."""
        try:
            with open(path, "wb") as f:
                f.write(audio_data)
        except Exception as e:
            print(f"Failed to save audio: {e}")
    
    def _play_audio(self, audio_data: bytes):
        """Play audio data using available audio player."""
        players = [
            (["mpv", "--no-video", "-"], "mpv"),
            (["mpg123", "-"], "mpg123"),
            (["ffplay", "-nodisp", "-autoexit", "-i", "pipe:0"], "ffplay"),
        ]
        
        for cmd, name in players:
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                proc.communicate(input=audio_data, timeout=30)
                if proc.returncode == 0:
                    return
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                continue
        
        print("No audio player available")


def get_tts_engine(voice: str = "texas", pitch_shift: int = 0) -> TTSEngine:
    """Get a TTS engine instance."""
    return TTSEngine(voice=voice, pitch_shift=pitch_shift)


def speak(text: str, voice: str = "texas", output_path: Optional[str] = None) -> dict:
    """Convenience function to speak text."""
    engine = get_tts_engine(voice=voice)
    return engine.speak(text, output_path)


def is_available() -> dict:
    """Check TTS engine availability."""
    return {
        "edge_tts": HAS_EDGE_TTS,
        "rvc": HAS_RVC,
        "model_files": {
            "pth": Path("voice_models/texas_arknights/texas_arknights_270.pth").exists(),
            "index": Path("voice_models/texas_arknights/added_IVF144_Flat_nprobe_1_texas_arknights_v2.index").exists()
        }
    }
