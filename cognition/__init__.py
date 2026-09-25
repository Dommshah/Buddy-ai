"""
Cognition Layer — the brain of the AI agent.
Provides reasoning, learning, creativity, security, voice, and more.
"""
from .reasoning.engine import ReasoningEngine, ReasoningMode, format_reasoning
from .learning.adaptive import LearningSystem
from .patterns import PatternRecognizer, PredictionEngine
from .voice import VoiceRecognition
from .security import SecurityAuditor
from .content import ContentCreator
from .code_analysis import CodeAnalyzer, CodeGenerator
from .creativity import CreativityEngine
from .autonomy import AutonomyController
from .verification import VerificationEngine

__all__ = [
    "ReasoningEngine", "ReasoningMode", "format_reasoning",
    "LearningSystem",
    "PatternRecognizer", "PredictionEngine",
    "VoiceRecognition",
    "SecurityAuditor",
    "ContentCreator",
    "CodeAnalyzer", "CodeGenerator",
    "CreativityEngine",
    "AutonomyController",
    "VerificationEngine",
]
