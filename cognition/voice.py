"""
Voice Module — Text-to-Speech, Speech Recognition, and Voice Conversation.
Provides human-like TTS and continuous listening capabilities.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import tempfile
import threading
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class VoiceConfig:
    """Configuration for voice features."""
    language: str = "en"
    sample_rate: int = 16000
    energy_threshold: int = 300
    pause_threshold: float = 1.5
    phrase_limit: int = 0  # 0 = unlimited until silence
    tts_rate: int = 150
    tts_volume: float = 0.9
    silence_threshold: float = 0.01
    max_silence_duration: float = 2.0


@dataclass
class VoiceRecognition:
    """Voice recognition and TTS system."""
    config: VoiceConfig = field(default_factory=VoiceConfig)
    _tts_lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _is_listening: bool = field(default=False, init=False)

    def get_status(self) -> dict[str, Any]:
        """Get current voice system status."""
        return {
            "tts_available": self._check_tts(),
            "stt_available": self._check_stt(),
            "mic_available": self._check_mic(),
        }

    def _check_tts(self) -> bool:
        """Check if TTS is available."""
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    def _check_stt(self) -> bool:
        """Check if STT is available."""
        try:
            import speech_recognition
            return True
        except ImportError:
            return False

    def _check_mic(self) -> bool:
        """Check if microphone is available."""
        try:
            result = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
            return "card" in result.stdout
        except Exception:
            return False

    # ── TEXT-TO-SPEECH ─────────────────────────────────────────────

    def speak(self, text: str, output_path: str | None = None) -> dict[str, Any]:
        """Convert text to speech using Texas Arknights voice model.
        
        Priority: TTS Engine (edge-tts + RVC) -> gTTS -> pyttsx3
        """
        with self._tts_lock:
            # Kill previous audio
            subprocess.run(["pkill", "-f", "mpg123.*mp3"], capture_output=True)
            subprocess.run(["pkill", "-f", "mpv.*mp3"], capture_output=True)
            
            # Try the advanced TTS engine with RVC
            try:
                from .tts_engine import speak as tts_speak
                result = tts_speak(text, voice="texas", output_path=output_path)
                if result.get("success"):
                    return result
            except ImportError:
                pass
            except Exception as e:
                print(f"TTS engine error: {e}")
            
            # Fallback to pyttsx3
            try:
                import pyttsx3
                engine = pyttsx3.init()
                
                voices = engine.getProperty('voices')
                for voice in voices:
                    if 'english' in voice.name.lower() or 'en' in voice.id.lower():
                        engine.setProperty('voice', voice.id)
                        break
                
                engine.setProperty('rate', self.config.tts_rate)
                engine.setProperty('volume', self.config.tts_volume)
                
                if output_path:
                    engine.save_to_file(text, output_path)
                    engine.runAndWait()
                    return {"success": True, "engine": "pyttsx3", "output": output_path}
                else:
                    engine.say(text)
                    engine.runAndWait()
                    return {"success": True, "engine": "pyttsx3"}
                    
            except Exception as e:
                return self._speak_gtts(text, output_path)

    def _speak_gtts(self, text: str, output_path: str | None = None) -> dict[str, Any]:
        """Fallback to gTTS."""
        try:
            from gtts import gTTS
            
            tts = gTTS(text=text, lang=self.config.language, slow=False)
            
            if output_path:
                tts.save(output_path)
                return {"success": True, "engine": "gtts", "output": output_path}
            else:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    temp_path = f.name
                tts.save(temp_path)
                
                subprocess.run(["pkill", "-f", "mpg123.*mp3"], capture_output=True)
                
                for player in ["mpg123", "mpv", "ffplay"]:
                    try:
                        if player == "mpg123":
                            proc = subprocess.Popen([player, "-q", temp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            proc.wait(timeout=30)
                        elif player == "mpv":
                            proc = subprocess.Popen([player, "--no-video", temp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            proc.wait(timeout=30)
                        elif player == "ffplay":
                            proc = subprocess.Popen([player, "-nodisp", "-autoexit", temp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            proc.wait(timeout=30)
                        
                        try:
                            Path(temp_path).unlink()
                        except Exception:
                            pass
                        return {"success": True, "engine": "gtts"}
                    except FileNotFoundError:
                        continue
                
                return {"success": False, "error": "No audio player available"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def text_to_speech(self, text: str, output_path: str | None = None) -> dict[str, Any]:
        """Legacy method for compatibility."""
        return self.speak(text, output_path)

    # ── SPEECH-TO-TEXT ─────────────────────────────────────────────

    def listen(self, timeout: int = 0, phrase_time_limit: int = 0) -> dict[str, Any]:
        """Listen from microphone with unlimited time until user stops speaking.
        
        Args:
            timeout: Max seconds to wait for speech to start (0=wait forever)
            phrase_time_limit: Max seconds for phrase (0=unlimited until silence)
        """
        self._is_listening = True
        
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = self.config.energy_threshold
            recognizer.pause_threshold = self.config.pause_threshold
            
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                if timeout > 0:
                    audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit if phrase_time_limit > 0 else None)
                else:
                    audio = recognizer.listen(source, phrase_time_limit=phrase_time_limit if phrase_time_limit > 0 else None)
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio.get_wav_data())
                tmp_path = tmp.name
            
            result = self._transcribe_file(tmp_path)
            Path(tmp_path).unlink(missing_ok=True)
            
            self._is_listening = False
            return result
            
        except ImportError:
            self._is_listening = False
            return {
                "success": False,
                "error": "SpeechRecognition not installed",
                "text": "",
            }
        except Exception as e:
            self._is_listening = False
            return self._listen_with_arecord()

    def listen_continuous(self, callback: Callable[[str], None], max_duration: int = 0) -> None:
        """Listen continuously and call callback with each recognized phrase.
        
        Args:
            callback: Function to call with each recognized text
            max_duration: Max seconds to listen (0=unlimited)
        """
        self._is_listening = True
        start_time = time.time()
        
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = self.config.energy_threshold
            recognizer.pause_threshold = self.config.pause_threshold
            
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print("🎤 Listening... (speak, I'll respond when you pause)")
                
                while self._is_listening:
                    if max_duration > 0 and (time.time() - start_time) > max_duration:
                        break
                    
                    try:
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=None)
                        
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                            tmp.write(audio.get_wav_data())
                            tmp_path = tmp.name
                        
                        result = self._transcribe_file(tmp_path)
                        Path(tmp_path).unlink(missing_ok=True)
                        
                        if result.get("success") and result.get("text"):
                            callback(result["text"])
                            
                    except sr.WaitTimeoutError:
                        continue
                    except Exception:
                        continue
                        
        except ImportError:
            print("⚠ SpeechRecognition not installed")
        except Exception as e:
            print(f"⚠ Listening error: {e}")
        finally:
            self._is_listening = False

    def stop_listening(self) -> None:
        """Stop continuous listening."""
        self._is_listening = False

    def _listen_with_arecord(self) -> dict[str, Any]:
        """Fallback: use arecord to capture audio."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            print("🎤 Listening... Speak now...")
            
            proc = subprocess.Popen(
                ["arecord", "-f", "S16_LE", "-r", "16000", "-c", "1", "-d", "10", temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate(timeout=15)
            
            if not Path(temp_path).exists() or Path(temp_path).stat().st_size < 1000:
                return {
                    "success": False,
                    "error": "No audio captured. Check microphone.",
                    "text": "",
                }
            
            result = self._transcribe_file(temp_path)
            
            try:
                Path(temp_path).unlink()
            except Exception:
                pass
            
            self._is_listening = False
            return result
            
        except Exception as e:
            self._is_listening = False
            return {"success": False, "error": f"Recording failed: {e}", "text": ""}

    def _transcribe_file(self, audio_path: str) -> dict[str, Any]:
        """Transcribe an audio file."""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            
            text = recognizer.recognize_google(audio, language=self.config.language)
            return {
                "success": True,
                "text": text,
                "engine": "google",
                "language": self.config.language,
            }
        except sr.UnknownValueError:
            return {"success": False, "error": "Could not understand audio", "text": ""}
        except sr.RequestError as e:
            return {"success": False, "error": f"API error: {e}", "text": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "text": ""}

    def transcribe_audio(self, audio_path: str) -> dict[str, Any]:
        """Transcribe an audio file (public method)."""
        return self._transcribe_file(audio_path)

    # ── VOICE CONVERSATION MODE ────────────────────────────────────

    def voice_chat(self, agent_chat_func: Callable[[str], str], on_speak: Callable[[str], None] | None = None) -> None:
        """Start a voice conversation with the agent.
        
        Args:
            agent_chat_func: Function that takes user text and returns agent response
            on_speak: Optional callback when agent speaks (for custom TTS)
        """
        self._is_listening = True
        
        print("\n" + "=" * 50)
        print("  🎤 VOICE MODE ACTIVATED")
        print("  Speak naturally - I'll listen until you pause")
        print("  Say 'quit voice' to exit voice mode")
        print("=" * 50 + "\n")
        
        while self._is_listening:
            try:
                print("🎤 Listening... (speak now)")
                
                result = self.listen(timeout=0, phrase_time_limit=0)
                
                if not result.get("success"):
                    if "Could not understand" in result.get("error", ""):
                        print("  (didn't catch that, try again)")
                        continue
                    else:
                        print(f"  Error: {result.get('error', 'Unknown')}")
                        continue
                
                user_text = result.get("text", "").strip()
                
                if not user_text:
                    continue
                
                print(f"\n👤 You: {user_text}")
                
                if user_text.lower() in ["quit voice", "exit voice", "stop voice"]:
                    print("\n🎤 Voice mode deactivated. Back to text mode.")
                    self._is_listening = False
                    break
                
                response = agent_chat_func(user_text)
                
                print(f"\n🤖 Kaka: {response}")
                
                if on_speak:
                    on_speak(response)
                else:
                    self.speak(response)
                    
            except KeyboardInterrupt:
                print("\n\n🎤 Voice mode stopped.")
                self._is_listening = False
                break
            except Exception as e:
                print(f"Error: {e}")
                continue

    # ── UTILITY ────────────────────────────────────────────────────

    def get_microphone_info(self) -> dict[str, Any]:
        """Get information about available microphones."""
        try:
            result = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
            devices = []
            for line in result.stdout.split("\n"):
                if "card" in line:
                    devices.append(line.strip())
            return {"available": len(devices) > 0, "devices": devices}
        except Exception:
            return {"available": False, "devices": []}
