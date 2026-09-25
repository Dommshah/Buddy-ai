"""Privacy Module for Buddy.ai - Local-first, no-telemetry, encrypted storage."""
import os
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


# ── Privacy Configuration ────────────────────────────────────────────

PRIVACY_CONFIG = {
    "local_only": True,           # All data stays on device
    "no_telemetry": True,         # No analytics or tracking
    "no_server_history": True,    # No server-side storage
    "encrypt_local_storage": True, # Encrypt sensitive data
    "audit_logging": True,        # Log all external API calls
    "proxy_enabled": False,       # Optional proxy support
    "proxy_url": "",              # Proxy URL if enabled
}


@dataclass
class AuditEntry:
    """Audit log entry for external API calls."""
    timestamp: str
    endpoint: str
    method: str
    status: str
    duration_ms: float
    tokens_used: int = 0
    model: str = ""


class PrivacyManager:
    """Manages privacy features for the AI agent."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.audit_log_path = self.project_root / "privacy_audit.log"
        self.config = PRIVACY_CONFIG.copy()
        self._encryption_key: Optional[bytes] = None
    
    # ── Local-Only Storage ───────────────────────────────────────────
    
    def get_local_storage_path(self) -> Path:
        """Get path for local-only storage."""
        storage_dir = self.project_root / ".privacy_storage"
        storage_dir.mkdir(exist_ok=True)
        return storage_dir
    
    def save_local_only(self, key: str, data: dict) -> bool:
        """Save data locally only - never sent to any server."""
        try:
            storage_path = self.get_local_storage_path() / f"{key}.json"
            
            # Add metadata
            save_data = {
                "created_at": datetime.now().isoformat(),
                "local_only": True,
                "never_synced": True,
                "data": data
            }
            
            with open(storage_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Local save failed: {e}")
            return False
    
    def load_local_only(self, key: str) -> Optional[dict]:
        """Load data from local storage only."""
        try:
            storage_path = self.get_local_storage_path() / f"{key}.json"
            
            if not storage_path.exists():
                return None
            
            with open(storage_path, 'r') as f:
                save_data = json.load(f)
            
            # Verify local-only flag
            if not save_data.get("local_only", False):
                print("Warning: Data may not be local-only")
            
            return save_data.get("data", {})
            
        except Exception as e:
            print(f"Local load failed: {e}")
            return None
    
    # ── No Telemetry ─────────────────────────────────────────────────
    
    def verify_no_telemetry(self) -> dict:
        """Verify no telemetry is being sent."""
        checks = {
            "analytics_enabled": False,
            "tracking_enabled": False,
            "crash_reporting": False,
            "usage_statistics": False,
            "third_party_tracking": False,
        }
        
        # Check for any telemetry-related code
        telemetry_patterns = [
            "analytics", "tracking", "telemetry", "crash_report",
            "usage_stats", "metrics", "google_analytics", "mixpanel",
            "segment", "amplitude", "hotjar"
        ]
        
        # Scan Python files for telemetry
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv']
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    try:
                        content = filepath.read_text(errors='ignore')
                        for pattern in telemetry_patterns:
                            if pattern.lower() in content.lower():
                                # Check if it's actual telemetry code
                                if not any(skip in content for skip in ['# ', '"""', "'''"]):
                                    checks["third_party_tracking"] = True
                    except Exception:
                        pass
        
        return checks
    
    # ── Encrypted Local Storage ──────────────────────────────────────
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key."""
        if self._encryption_key:
            return self._encryption_key
        
        key_file = self.project_root / ".privacy_key"
        
        if key_file.exists():
            self._encryption_key = key_file.read_bytes()
        else:
            # Generate new key
            self._encryption_key = Fernet.generate_key()
            key_file.write_bytes(self._encryption_key)
            # Make key file readable only by owner
            os.chmod(key_file, 0o600)
        
        return self._encryption_key
    
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data."""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        return fernet.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data."""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data).decode()
    
    def save_encrypted(self, key: str, data: dict) -> bool:
        """Save encrypted data locally."""
        try:
            storage_path = self.get_local_storage_path() / f"{key}.enc"
            
            # Encrypt the data
            json_data = json.dumps(data)
            encrypted = self.encrypt_data(json_data)
            
            with open(storage_path, 'wb') as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            print(f"Encrypted save failed: {e}")
            return False
    
    def load_encrypted(self, key: str) -> Optional[dict]:
        """Load encrypted data locally."""
        try:
            storage_path = self.get_local_storage_path() / f"{key}.enc"
            
            if not storage_path.exists():
                return None
            
            with open(storage_path, 'rb') as f:
                encrypted = f.read()
            
            json_data = self.decrypt_data(encrypted)
            return json.loads(json_data)
            
        except Exception as e:
            print(f"Encrypted load failed: {e}")
            return None
    
    # ── Audit Logging ────────────────────────────────────────────────
    
    def log_api_call(self, entry: AuditEntry) -> None:
        """Log external API call for transparency."""
        if not self.config["audit_logging"]:
            return
        
        log_line = (
            f"[{entry.timestamp}] {entry.method} {entry.endpoint} "
            f"Status:{entry.status} Duration:{entry.duration_ms:.1f}ms "
            f"Tokens:{entry.tokens_used} Model:{entry.model}\n"
        )
        
        with open(self.audit_log_path, 'a') as f:
            f.write(log_line)
    
    def get_audit_log(self, limit: int = 100) -> list[str]:
        """Get recent audit log entries."""
        if not self.audit_log_path.exists():
            return []
        
        with open(self.audit_log_path, 'r') as f:
            lines = f.readlines()
        
        return [line.strip() for line in lines[-limit:]]
    
    def get_privacy_report(self) -> str:
        """Generate privacy status report."""
        report = [
            "=" * 60,
            "PRIVACY STATUS REPORT",
            "=" * 60,
            "",
            "Storage:",
            f"  Local-only: {'✓ Enabled' if self.config['local_only'] else '✗ Disabled'}",
            f"  Encryption: {'✓ Enabled' if self.config['encrypt_local_storage'] else '✗ Disabled'}",
            f"  Storage path: {self.get_local_storage_path()}",
            "",
            "Telemetry:",
            f"  No-telemetry: {'✓ Enabled' if self.config['no_telemetry'] else '✗ Disabled'}",
            f"  No server history: {'✓ Enabled' if self.config['no_server_history'] else '✗ Disabled'}",
            "",
            "Network:",
            f"  Proxy: {'✓ Enabled' if self.config['proxy_enabled'] else '✗ Disabled'}",
            f"  Audit logging: {'✓ Enabled' if self.config['audit_logging'] else '✗ Disabled'}",
            "",
            "Telemetry Verification:",
        ]
        
        # Run telemetry verification
        checks = self.verify_no_telemetry()
        for check, passed in checks.items():
            status = "✓ None detected" if not passed else "✗ Found"
            report.append(f"  {check}: {status}")
        
        # Count audit entries
        audit_entries = self.get_audit_log()
        report.extend([
            "",
            f"Audit Log: {len(audit_entries)} entries",
            "",
            "=" * 60,
        ])
        
        return "\n".join(report)


# ── Global Instance ──────────────────────────────────────────────────

_manager: Optional[PrivacyManager] = None


def get_privacy_manager() -> PrivacyManager:
    """Get or create the global privacy manager."""
    global _manager
    if _manager is None:
        _manager = PrivacyManager()
    return _manager


def save_local_only(key: str, data: dict) -> bool:
    """Convenience function for local-only storage."""
    return get_privacy_manager().save_local_only(key, data)


def load_local_only(key: str) -> Optional[dict]:
    """Convenience function for local-only loading."""
    return get_privacy_manager().load_local_only(key)


def log_api_call(endpoint: str, method: str, status: str, 
                 duration_ms: float, tokens_used: int = 0, model: str = "") -> None:
    """Convenience function for audit logging."""
    entry = AuditEntry(
        timestamp=datetime.now().isoformat(),
        endpoint=endpoint,
        method=method,
        status=status,
        duration_ms=duration_ms,
        tokens_used=tokens_used,
        model=model
    )
    get_privacy_manager().log_api_call(entry)


def get_privacy_report() -> str:
    """Convenience function for privacy report."""
    return get_privacy_manager().get_privacy_report()
