#!/usr/bin/env python3
"""
Smart AI Session Management Commands
Comprehensive session management system for smart-ai CLI with conversation history,
state persistence, and advanced session features following Claude Code patterns.
"""

import asyncio
import json
import hashlib
import os
import time
import shutil
import zipfile
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

# Session file format and encryption imports
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    print("Warning: cryptography library not available. Session encryption disabled.")

# Import smart-ai components
from smart_ai_slash_commands import (
    BaseCommandHandler, CommandDefinition, CommandCategory, 
    CommandParameter, ParsedCommand, CommandExecutionContext,
    command_error_handler
)
from smart_ai_notifications import NotificationManager, NotificationType


class SessionStatus(Enum):
    """Session status types"""
    ACTIVE = "active"
    SAVED = "saved" 
    ARCHIVED = "archived"
    CORRUPTED = "corrupted"
    ENCRYPTED = "encrypted"
    TEMPORARY = "temporary"


class ExportFormat(Enum):
    """Session export formats"""
    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    ZIP = "zip"


@dataclass
class ConversationEntry:
    """Represents a single conversation entry"""
    id: str
    timestamp: datetime
    role: str  # user, assistant, system
    content: str
    provider: Optional[str] = None
    tokens_used: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'role': self.role,
            'content': self.content,
            'provider': self.provider,
            'tokens_used': self.tokens_used,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationEntry':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            role=data['role'],
            content=data['content'],
            provider=data.get('provider'),
            tokens_used=data.get('tokens_used'),
            metadata=data.get('metadata', {})
        )


@dataclass 
class SessionMetadata:
    """Session metadata and configuration"""
    name: str
    created_at: datetime
    last_modified: datetime
    description: str = ""
    tags: List[str] = field(default_factory=list)
    project_root: Optional[str] = None
    provider_states: Dict[str, Any] = field(default_factory=dict)
    mcp_config: Dict[str, Any] = field(default_factory=dict)
    conversation_count: int = 0
    total_tokens: int = 0
    version: str = "1.0"
    status: SessionStatus = SessionStatus.ACTIVE
    encrypted: bool = False
    compression: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'description': self.description,
            'tags': self.tags,
            'project_root': self.project_root,
            'provider_states': self.provider_states,
            'mcp_config': self.mcp_config,
            'conversation_count': self.conversation_count,
            'total_tokens': self.total_tokens,
            'version': self.version,
            'status': self.status.value,
            'encrypted': self.encrypted,
            'compression': self.compression
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetadata':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_modified=datetime.fromisoformat(data['last_modified']),
            description=data.get('description', ''),
            tags=data.get('tags', []),
            project_root=data.get('project_root'),
            provider_states=data.get('provider_states', {}),
            mcp_config=data.get('mcp_config', {}),
            conversation_count=data.get('conversation_count', 0),
            total_tokens=data.get('total_tokens', 0),
            version=data.get('version', '1.0'),
            status=SessionStatus(data.get('status', 'active')),
            encrypted=data.get('encrypted', False),
            compression=data.get('compression', False)
        )


@dataclass
class SessionData:
    """Complete session data structure"""
    metadata: SessionMetadata
    conversation_history: List[ConversationEntry] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'metadata': self.metadata.to_dict(),
            'conversation_history': [entry.to_dict() for entry in self.conversation_history],
            'context_data': self.context_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary"""
        return cls(
            metadata=SessionMetadata.from_dict(data['metadata']),
            conversation_history=[
                ConversationEntry.from_dict(entry) 
                for entry in data.get('conversation_history', [])
            ],
            context_data=data.get('context_data', {})
        )


class SessionEncryption:
    """Handles session encryption and decryption"""
    
    def __init__(self, password: Optional[str] = None):
        self.password = password
        self.salt = b'smart_ai_session_salt_2024'  # Should be random in production
        
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt_data(self, data: str, password: str) -> bytes:
        """Encrypt session data"""
        if not ENCRYPTION_AVAILABLE:
            raise ValueError("Encryption not available - install cryptography package")
        
        key = self._derive_key(password)
        fernet = Fernet(key)
        return fernet.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes, password: str) -> str:
        """Decrypt session data"""
        if not ENCRYPTION_AVAILABLE:
            raise ValueError("Encryption not available - install cryptography package")
        
        key = self._derive_key(password)
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data).decode()


class SessionStorage:
    """Handles session file storage and management"""
    
    def __init__(self, sessions_dir: Optional[Path] = None):
        self.sessions_dir = sessions_dir or Path.home() / ".smart-ai" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.encryption = SessionEncryption()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def save_session(self, session_data: SessionData, password: Optional[str] = None) -> Path:
        """Save session to file with optional encryption"""
        session_name = session_data.metadata.name
        
        # Update metadata
        session_data.metadata.last_modified = datetime.now()
        session_data.metadata.conversation_count = len(session_data.conversation_history)
        session_data.metadata.total_tokens = sum(
            entry.tokens_used or 0 for entry in session_data.conversation_history
        )
        
        # Convert to JSON
        json_data = json.dumps(session_data.to_dict(), indent=2, default=str)
        
        # Handle encryption
        if password and ENCRYPTION_AVAILABLE:
            session_data.metadata.encrypted = True
            encrypted_data = self.encryption.encrypt_data(json_data, password)
            file_path = self.sessions_dir / f"{session_name}.session.enc"
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
        else:
            file_path = self.sessions_dir / f"{session_name}.session.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
        
        self.logger.info(f"Session saved: {file_path}")
        return file_path
    
    def load_session(self, session_name: str, password: Optional[str] = None) -> SessionData:
        """Load session from file with optional decryption"""
        # Try encrypted file first
        enc_path = self.sessions_dir / f"{session_name}.session.enc"
        json_path = self.sessions_dir / f"{session_name}.session.json"
        
        if enc_path.exists():
            if not password:
                raise ValueError("Password required for encrypted session")
            
            with open(enc_path, 'rb') as f:
                encrypted_data = f.read()
            
            json_data = self.encryption.decrypt_data(encrypted_data, password)
        elif json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = f.read()
        else:
            raise FileNotFoundError(f"Session '{session_name}' not found")
        
        data = json.loads(json_data)
        return SessionData.from_dict(data)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions with metadata"""
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.session.*"):
            try:
                if session_file.suffix == '.enc':
                    session_name = session_file.stem.replace('.session', '')
                    encrypted = True
                    # Can't read metadata without password
                    sessions.append({
                        'name': session_name,
                        'encrypted': encrypted,
                        'file_path': str(session_file),
                        'size': session_file.stat().st_size,
                        'modified': datetime.fromtimestamp(session_file.stat().st_mtime)
                    })
                else:
                    session_name = session_file.stem.replace('.session', '')
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = SessionMetadata.from_dict(data['metadata'])
                    sessions.append({
                        'name': session_name,
                        'encrypted': False,
                        'file_path': str(session_file),
                        'size': session_file.stat().st_size,
                        'modified': metadata.last_modified,
                        'metadata': metadata
                    })
            except Exception as e:
                self.logger.warning(f"Could not read session {session_file}: {e}")
        
        return sorted(sessions, key=lambda x: x['modified'], reverse=True)
    
    def delete_session(self, session_name: str) -> bool:
        """Delete a session file"""
        enc_path = self.sessions_dir / f"{session_name}.session.enc"
        json_path = self.sessions_dir / f"{session_name}.session.json"
        
        deleted = False
        if enc_path.exists():
            enc_path.unlink()
            deleted = True
        if json_path.exists():
            json_path.unlink()
            deleted = True
        
        return deleted
    
    def archive_session(self, session_name: str, archive_dir: Optional[Path] = None) -> Path:
        """Archive a session to separate directory"""
        archive_dir = archive_dir or self.sessions_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        # Find session file
        enc_path = self.sessions_dir / f"{session_name}.session.enc"
        json_path = self.sessions_dir / f"{session_name}.session.json"
        
        source_path = enc_path if enc_path.exists() else json_path
        if not source_path.exists():
            raise FileNotFoundError(f"Session '{session_name}' not found")
        
        # Move to archive
        dest_path = archive_dir / source_path.name
        shutil.move(str(source_path), str(dest_path))
        
        return dest_path


class SessionExporter:
    """Handles session export in various formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_session(self, session_data: SessionData, format_type: ExportFormat, 
                      output_path: Path, include_metadata: bool = True) -> Path:
        """Export session in specified format"""
        if format_type == ExportFormat.JSON:
            return self._export_json(session_data, output_path, include_metadata)
        elif format_type == ExportFormat.TEXT:
            return self._export_text(session_data, output_path)
        elif format_type == ExportFormat.MARKDOWN:
            return self._export_markdown(session_data, output_path)
        elif format_type == ExportFormat.HTML:
            return self._export_html(session_data, output_path)
        elif format_type == ExportFormat.ZIP:
            return self._export_zip(session_data, output_path, include_metadata)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_json(self, session_data: SessionData, output_path: Path, include_metadata: bool) -> Path:
        """Export as JSON"""
        data = session_data.to_dict()
        if not include_metadata:
            data.pop('metadata', None)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        return output_path
    
    def _export_text(self, session_data: SessionData, output_path: Path) -> Path:
        """Export as plain text"""
        lines = []
        lines.append(f"Session: {session_data.metadata.name}")
        lines.append(f"Created: {session_data.metadata.created_at}")
        lines.append(f"Description: {session_data.metadata.description}")
        lines.append("=" * 50)
        lines.append("")
        
        for entry in session_data.conversation_history:
            timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            provider_info = f" [{entry.provider}]" if entry.provider else ""
            lines.append(f"[{timestamp}] {entry.role.upper()}{provider_info}:")
            lines.append(entry.content)
            lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return output_path
    
    def _export_markdown(self, session_data: SessionData, output_path: Path) -> Path:
        """Export as Markdown"""
        lines = []
        lines.append(f"# Session: {session_data.metadata.name}")
        lines.append("")
        lines.append(f"**Created:** {session_data.metadata.created_at}")
        lines.append(f"**Description:** {session_data.metadata.description}")
        lines.append(f"**Conversations:** {len(session_data.conversation_history)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        for entry in session_data.conversation_history:
            timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            provider_info = f" `{entry.provider}`" if entry.provider else ""
            
            if entry.role == "user":
                lines.append(f"## 👤 User{provider_info}")
                lines.append(f"*{timestamp}*")
                lines.append("")
                lines.append(entry.content)
            elif entry.role == "assistant":
                lines.append(f"## 🤖 Assistant{provider_info}")
                lines.append(f"*{timestamp}*")
                lines.append("")
                lines.append(entry.content)
            else:
                lines.append(f"## 🔧 System{provider_info}")
                lines.append(f"*{timestamp}*")
                lines.append("")
                lines.append(f"```\n{entry.content}\n```")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return output_path
    
    def _export_html(self, session_data: SessionData, output_path: Path) -> Path:
        """Export as HTML"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Session: {html.escape(session_data.metadata.name)}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }}
        .conversation {{ margin-bottom: 30px; padding: 20px; border-radius: 8px; }}
        .user {{ background: #f0f9ff; border-left: 4px solid #0ea5e9; }}
        .assistant {{ background: #f0fdf4; border-left: 4px solid #22c55e; }}
        .system {{ background: #fef3c7; border-left: 4px solid #f59e0b; }}
        .timestamp {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
        .provider {{ color: #0ea5e9; font-weight: bold; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }}
        .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Session: {html.escape(session_data.metadata.name)}</h1>
        <div class="metadata">
            <strong>Created:</strong> {session_data.metadata.created_at}<br>
            <strong>Description:</strong> {html.escape(session_data.metadata.description)}<br>
            <strong>Conversations:</strong> {len(session_data.conversation_history)}<br>
            <strong>Total Tokens:</strong> {session_data.metadata.total_tokens}
        </div>
    </div>
"""
        
        for entry in session_data.conversation_history:
            timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            provider_info = f'<span class="provider">[{entry.provider}]</span>' if entry.provider else ""
            role_class = entry.role
            role_display = {"user": "👤 User", "assistant": "🤖 Assistant", "system": "🔧 System"}[entry.role]
            
            content = html.escape(entry.content).replace('\n', '<br>')
            
            html_content += f"""
    <div class="conversation {role_class}">
        <div class="timestamp">{timestamp} - {role_display} {provider_info}</div>
        <div>{content}</div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _export_zip(self, session_data: SessionData, output_path: Path, include_metadata: bool) -> Path:
        """Export as ZIP archive with multiple formats"""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            base_name = session_data.metadata.name
            
            # Export in multiple formats
            self._export_json(session_data, temp_path / f"{base_name}.json", include_metadata)
            self._export_text(session_data, temp_path / f"{base_name}.txt")
            self._export_markdown(session_data, temp_path / f"{base_name}.md")
            self._export_html(session_data, temp_path / f"{base_name}.html")
            
            # Create ZIP
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.iterdir():
                    zipf.write(file_path, file_path.name)
        
        return output_path


class SessionCompactor:
    """Handles conversation compacting and summarization"""
    
    def __init__(self, smart_ai_backend=None):
        self.backend = smart_ai_backend
        self.logger = logging.getLogger(__name__)
    
    async def compact_session(self, session_data: SessionData, instructions: Optional[str] = None,
                            preserve_recent: int = 10) -> SessionData:
        """Compact session conversation history with AI summarization"""
        if len(session_data.conversation_history) <= preserve_recent:
            return session_data  # Nothing to compact
        
        # Split into sections to compact and preserve
        to_compact = session_data.conversation_history[:-preserve_recent]
        to_preserve = session_data.conversation_history[-preserve_recent:]
        
        # Create summary prompt
        summary_prompt = self._create_summary_prompt(to_compact, instructions)
        
        # Get AI summary if backend available
        if self.backend:
            try:
                provider = self.backend.handle_provider_fallback(prompt=summary_prompt)
                if provider:
                    summary_response = await self.backend.process_request_async(summary_prompt, provider)
                    if summary_response:
                        summary = self.backend.get_clean_output(summary_response)
                    else:
                        summary = "Summary generation failed"
                else:
                    summary = "No AI provider available for summary"
            except Exception as e:
                self.logger.warning(f"AI summary failed: {e}")
                summary = self._create_simple_summary(to_compact)
        else:
            summary = self._create_simple_summary(to_compact)
        
        # Create summary entry
        summary_entry = ConversationEntry(
            id=f"summary_{int(time.time())}",
            timestamp=datetime.now(),
            role="system",
            content=f"CONVERSATION SUMMARY:\n{summary}",
            metadata={
                'type': 'summary',
                'original_entries': len(to_compact),
                'compact_instructions': instructions
            }
        )
        
        # Create new session data
        compacted_session = SessionData(
            metadata=session_data.metadata,
            conversation_history=[summary_entry] + to_preserve,
            context_data=session_data.context_data
        )
        
        # Update metadata
        compacted_session.metadata.last_modified = datetime.now()
        compacted_session.metadata.conversation_count = len(compacted_session.conversation_history)
        
        return compacted_session
    
    def _create_summary_prompt(self, entries: List[ConversationEntry], instructions: Optional[str]) -> str:
        """Create prompt for AI summarization"""
        conversation_text = []
        for entry in entries:
            role_display = entry.role.upper()
            provider_info = f" [{entry.provider}]" if entry.provider else ""
            conversation_text.append(f"{role_display}{provider_info}: {entry.content}")
        
        base_prompt = f"""
Please create a concise summary of the following conversation history.
Focus on key topics discussed, important decisions made, and relevant context.

{instructions or "Preserve important technical details and user preferences."}

CONVERSATION TO SUMMARIZE:
{''.join(conversation_text[:5000])}  # Limit for context window

Provide a structured summary that captures the essential information.
"""
        return base_prompt
    
    def _create_simple_summary(self, entries: List[ConversationEntry]) -> str:
        """Create simple text-based summary when AI not available"""
        summary_parts = [
            f"Conversation from {entries[0].timestamp.strftime('%Y-%m-%d %H:%M')} to {entries[-1].timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"Total entries: {len(entries)}",
            "",
            "Key interactions:"
        ]
        
        # Sample key entries
        sample_size = min(5, len(entries))
        step = len(entries) // sample_size if sample_size > 0 else 1
        
        for i in range(0, len(entries), step):
            if len(summary_parts) > 20:  # Limit summary length
                break
            entry = entries[i]
            content_preview = entry.content[:100] + "..." if len(entry.content) > 100 else entry.content
            summary_parts.append(f"- {entry.role}: {content_preview}")
        
        return "\n".join(summary_parts)


class SessionMemoryManager:
    """Manages project memory and CLAUDE.md integration"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.claude_md_path = self.project_root / "CLAUDE.md"
        self.memory_dir = self.project_root / ".claude" / "memory"
        self.logger = logging.getLogger(__name__)
    
    def load_project_memory(self) -> Dict[str, str]:
        """Load project memory from CLAUDE.md and memory files"""
        memory = {}
        
        # Load main CLAUDE.md
        if self.claude_md_path.exists():
            memory['CLAUDE.md'] = self.claude_md_path.read_text(encoding='utf-8')
        
        # Load memory files
        if self.memory_dir.exists():
            for memory_file in self.memory_dir.glob("*.md"):
                memory[memory_file.name] = memory_file.read_text(encoding='utf-8')
        
        return memory
    
    def save_memory_entry(self, name: str, content: str) -> Path:
        """Save a memory entry"""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        if name == "CLAUDE.md":
            file_path = self.claude_md_path
        else:
            if not name.endswith('.md'):
                name += '.md'
            file_path = self.memory_dir / name
        
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def update_claude_md(self, session_data: SessionData, append: bool = True) -> None:
        """Update CLAUDE.md with session insights"""
        if not self.claude_md_path.exists() and not append:
            # Create new CLAUDE.md
            template = f"""# Project Memory

## Session: {session_data.metadata.name}
Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Key Insights
{self._extract_session_insights(session_data)}

### Provider Preferences
{self._extract_provider_preferences(session_data)}

### Development Patterns
{self._extract_development_patterns(session_data)}
"""
            self.claude_md_path.write_text(template, encoding='utf-8')
        elif append and self.claude_md_path.exists():
            # Append session summary
            existing_content = self.claude_md_path.read_text(encoding='utf-8')
            
            session_summary = f"""
## Session Update: {session_data.metadata.name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{self._extract_session_insights(session_data)}

"""
            
            # Append to existing content
            updated_content = existing_content + session_summary
            self.claude_md_path.write_text(updated_content, encoding='utf-8')
    
    def _extract_session_insights(self, session_data: SessionData) -> str:
        """Extract key insights from session"""
        insights = []
        
        # Analyze conversation patterns
        user_entries = [e for e in session_data.conversation_history if e.role == "user"]
        assistant_entries = [e for e in session_data.conversation_history if e.role == "assistant"]
        
        insights.append(f"- {len(user_entries)} user interactions")
        insights.append(f"- {len(assistant_entries)} assistant responses")
        
        # Provider usage
        providers = set(e.provider for e in session_data.conversation_history if e.provider)
        if providers:
            insights.append(f"- Providers used: {', '.join(providers)}")
        
        # Token usage
        if session_data.metadata.total_tokens > 0:
            insights.append(f"- Total tokens used: {session_data.metadata.total_tokens}")
        
        return "\n".join(insights)
    
    def _extract_provider_preferences(self, session_data: SessionData) -> str:
        """Extract provider usage patterns"""
        provider_counts = {}
        for entry in session_data.conversation_history:
            if entry.provider:
                provider_counts[entry.provider] = provider_counts.get(entry.provider, 0) + 1
        
        if not provider_counts:
            return "No specific provider preferences identified."
        
        preferences = []
        for provider, count in sorted(provider_counts.items(), key=lambda x: x[1], reverse=True):
            preferences.append(f"- {provider}: {count} uses")
        
        return "\n".join(preferences)
    
    def _extract_development_patterns(self, session_data: SessionData) -> str:
        """Extract development patterns from conversation"""
        patterns = []
        
        # Look for common development keywords
        dev_keywords = {
            'debugging': ['debug', 'error', 'bug', 'fix'],
            'implementation': ['implement', 'create', 'build', 'develop'],
            'testing': ['test', 'testing', 'pytest', 'unittest'],
            'refactoring': ['refactor', 'optimize', 'improve', 'restructure']
        }
        
        keyword_counts = {category: 0 for category in dev_keywords}
        
        for entry in session_data.conversation_history:
            content_lower = entry.content.lower()
            for category, keywords in dev_keywords.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        keyword_counts[category] += 1
        
        for category, count in keyword_counts.items():
            if count > 0:
                patterns.append(f"- {category.title()}: {count} mentions")
        
        return "\n".join(patterns) if patterns else "No specific development patterns identified."


# Command Handlers

class SaveSessionCommandHandler(BaseCommandHandler):
    """Handler for /save command"""
    
    def __init__(self, storage: SessionStorage, notification_manager: Optional[NotificationManager] = None):
        self.storage = storage
        self.notification_manager = notification_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        session_name = parsed_cmd.args[0] if parsed_cmd.args else f"session_{int(time.time())}"
        password = parsed_cmd.kwargs.get('password')
        description = parsed_cmd.kwargs.get('description', '')
        compress = parsed_cmd.kwargs.get('compress', False)
        
        # Create session data from current context
        session_data = self._create_session_data(session_name, description, context)
        session_data.metadata.compression = compress
        
        try:
            file_path = self.storage.save_session(session_data, password)
            
            if self.notification_manager:
                self.notification_manager.notify(
                    "Session Saved",
                    f"Session '{session_name}' saved successfully",
                    NotificationType.SUCCESS
                )
            
            return f"✅ Session '{session_name}' saved to {file_path}"
            
        except Exception as e:
            if self.notification_manager:
                self.notification_manager.notify(
                    "Session Save Failed", 
                    str(e),
                    NotificationType.ERROR
                )
            raise
    
    def _create_session_data(self, name: str, description: str, context: CommandExecutionContext) -> SessionData:
        """Create session data from current context"""
        now = datetime.now()
        
        # Get conversation history from context (if available)
        conversation_history = []
        if hasattr(context.smart_ai, 'conversation_history'):
            conversation_history = context.smart_ai.conversation_history
        
        # Create metadata
        metadata = SessionMetadata(
            name=name,
            created_at=now,
            last_modified=now,
            description=description,
            project_root=str(context.project_root),
            provider_states=getattr(context.smart_ai, 'provider_states', {}),
            mcp_config=getattr(context.smart_ai, 'mcp_config', {}),
            status=SessionStatus.SAVED
        )
        
        return SessionData(
            metadata=metadata,
            conversation_history=conversation_history,
            context_data=context.session_data.copy()
        )


class LoadSessionCommandHandler(BaseCommandHandler):
    """Handler for /load command"""
    
    def __init__(self, storage: SessionStorage, notification_manager: Optional[NotificationManager] = None):
        self.storage = storage
        self.notification_manager = notification_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        if not parsed_cmd.args:
            return "❌ Session name required. Usage: /load <session_name>"
        
        session_name = parsed_cmd.args[0]
        password = parsed_cmd.kwargs.get('password')
        merge = parsed_cmd.kwargs.get('merge', False)
        
        try:
            session_data = self.storage.load_session(session_name, password)
            
            if merge:
                # Merge with current session
                self._merge_session_data(session_data, context)
                result_msg = f"✅ Session '{session_name}' merged with current session"
            else:
                # Replace current session
                self._load_session_data(session_data, context)
                result_msg = f"✅ Session '{session_name}' loaded successfully"
            
            if self.notification_manager:
                self.notification_manager.notify(
                    "Session Loaded",
                    f"Session '{session_name}' loaded",
                    NotificationType.SUCCESS
                )
            
            return result_msg
            
        except FileNotFoundError:
            return f"❌ Session '{session_name}' not found"
        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            if self.notification_manager:
                self.notification_manager.notify(
                    "Session Load Failed",
                    str(e),
                    NotificationType.ERROR
                )
            raise
    
    def _load_session_data(self, session_data: SessionData, context: CommandExecutionContext):
        """Load session data into current context"""
        # Update context session data
        context.session_data.clear()
        context.session_data.update(session_data.context_data)
        
        # Update smart AI instance
        if hasattr(context.smart_ai, 'conversation_history'):
            context.smart_ai.conversation_history = session_data.conversation_history
        
        if hasattr(context.smart_ai, 'provider_states'):
            context.smart_ai.provider_states = session_data.metadata.provider_states
        
        if hasattr(context.smart_ai, 'mcp_config'):
            context.smart_ai.mcp_config = session_data.metadata.mcp_config
    
    def _merge_session_data(self, session_data: SessionData, context: CommandExecutionContext):
        """Merge session data with current context"""
        # Merge conversation history
        if hasattr(context.smart_ai, 'conversation_history'):
            context.smart_ai.conversation_history.extend(session_data.conversation_history)
        
        # Merge context data
        context.session_data.update(session_data.context_data)


class ListSessionsCommandHandler(BaseCommandHandler):
    """Handler for /sessions command"""
    
    def __init__(self, storage: SessionStorage):
        self.storage = storage
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        verbose = parsed_cmd.kwargs.get('verbose', False)
        format_type = parsed_cmd.kwargs.get('format', 'table')
        
        sessions = self.storage.list_sessions()
        
        if not sessions:
            return "No saved sessions found."
        
        if format_type == 'json':
            return json.dumps([
                {k: v.isoformat() if isinstance(v, datetime) else v for k, v in session.items()}
                for session in sessions
            ], indent=2)
        
        # Table format
        lines = ["Available Sessions:", "=" * 50]
        
        for session in sessions:
            name = session['name']
            encrypted = "🔒" if session['encrypted'] else "📄"
            size_kb = session['size'] / 1024
            modified = session['modified'].strftime("%Y-%m-%d %H:%M")
            
            session_line = f"{encrypted} {name:20} {size_kb:6.1f}KB {modified}"
            
            if verbose and 'metadata' in session:
                metadata = session['metadata']
                description = metadata.description[:50] if metadata.description else "No description"
                session_line += f"\n     Description: {description}"
                session_line += f"\n     Conversations: {metadata.conversation_count}"
                if metadata.tags:
                    session_line += f"\n     Tags: {', '.join(metadata.tags)}"
            
            lines.append(session_line)
            if verbose:
                lines.append("")
        
        return "\n".join(lines)


class DeleteSessionCommandHandler(BaseCommandHandler):
    """Handler for /delete command"""
    
    def __init__(self, storage: SessionStorage, notification_manager: Optional[NotificationManager] = None):
        self.storage = storage
        self.notification_manager = notification_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        if not parsed_cmd.args:
            return "❌ Session name required. Usage: /delete <session_name>"
        
        session_name = parsed_cmd.args[0]
        force = parsed_cmd.kwargs.get('force', False)
        
        # Confirmation if not forced
        if not force:
            # In a real implementation, this would prompt the user
            # For now, we'll require --force flag
            return f"❌ Use --force to confirm deletion of session '{session_name}'"
        
        try:
            if self.storage.delete_session(session_name):
                if self.notification_manager:
                    self.notification_manager.notify(
                        "Session Deleted",
                        f"Session '{session_name}' deleted",
                        NotificationType.WARNING
                    )
                return f"✅ Session '{session_name}' deleted successfully"
            else:
                return f"❌ Session '{session_name}' not found"
        except Exception as e:
            if self.notification_manager:
                self.notification_manager.notify(
                    "Session Delete Failed",
                    str(e),
                    NotificationType.ERROR
                )
            raise


class ExportSessionCommandHandler(BaseCommandHandler):
    """Handler for /export command"""
    
    def __init__(self, storage: SessionStorage, exporter: SessionExporter):
        self.storage = storage
        self.exporter = exporter
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        session_name = parsed_cmd.args[0] if parsed_cmd.args else "current"
        format_type = ExportFormat(parsed_cmd.kwargs.get('format', 'json'))
        output_path = parsed_cmd.kwargs.get('output')
        include_metadata = parsed_cmd.kwargs.get('metadata', True)
        password = parsed_cmd.kwargs.get('password')
        
        # Load session data
        if session_name == "current":
            # Export current session
            session_data = self._create_current_session_data(context)
        else:
            session_data = self.storage.load_session(session_name, password)
        
        # Generate output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = format_type.value
            output_path = f"{session_name}_export_{timestamp}.{extension}"
        
        output_path = Path(output_path)
        
        try:
            exported_path = self.exporter.export_session(
                session_data, format_type, output_path, include_metadata
            )
            return f"✅ Session exported to {exported_path}"
        except Exception as e:
            return f"❌ Export failed: {e}"
    
    def _create_current_session_data(self, context: CommandExecutionContext) -> SessionData:
        """Create session data from current context"""
        now = datetime.now()
        
        metadata = SessionMetadata(
            name="current_session",
            created_at=now,
            last_modified=now,
            description="Current session export",
            project_root=str(context.project_root),
            status=SessionStatus.ACTIVE
        )
        
        conversation_history = getattr(context.smart_ai, 'conversation_history', [])
        
        return SessionData(
            metadata=metadata,
            conversation_history=conversation_history,
            context_data=context.session_data.copy()
        )


class ImportSessionCommandHandler(BaseCommandHandler):
    """Handler for /import command"""
    
    def __init__(self, storage: SessionStorage):
        self.storage = storage
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        if not parsed_cmd.args:
            return "❌ File path required. Usage: /import <file_path>"
        
        file_path = Path(parsed_cmd.args[0])
        session_name = parsed_cmd.kwargs.get('name')
        merge = parsed_cmd.kwargs.get('merge', False)
        
        if not file_path.exists():
            return f"❌ File not found: {file_path}"
        
        try:
            # Determine file format and load
            if file_path.suffix.lower() == '.json':
                session_data = self._import_json(file_path, session_name)
            else:
                return f"❌ Unsupported file format: {file_path.suffix}"
            
            if merge:
                # Merge with current session
                self._merge_imported_session(session_data, context)
                return f"✅ Session data from {file_path} merged successfully"
            else:
                # Save as new session
                self.storage.save_session(session_data)
                return f"✅ Session '{session_data.metadata.name}' imported from {file_path}"
                
        except Exception as e:
            return f"❌ Import failed: {e}"
    
    def _import_json(self, file_path: Path, session_name: Optional[str]) -> SessionData:
        """Import session from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        session_data = SessionData.from_dict(data)
        
        if session_name:
            session_data.metadata.name = session_name
        
        session_data.metadata.last_modified = datetime.now()
        return session_data
    
    def _merge_imported_session(self, session_data: SessionData, context: CommandExecutionContext):
        """Merge imported session with current context"""
        if hasattr(context.smart_ai, 'conversation_history'):
            context.smart_ai.conversation_history.extend(session_data.conversation_history)
        
        context.session_data.update(session_data.context_data)


class CompactSessionCommandHandler(BaseCommandHandler):
    """Handler for /compact command"""
    
    def __init__(self, compactor: SessionCompactor, storage: SessionStorage):
        self.compactor = compactor
        self.storage = storage
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        instructions = " ".join(parsed_cmd.args) if parsed_cmd.args else None
        preserve_recent = parsed_cmd.kwargs.get('keep', 10)
        save_backup = parsed_cmd.kwargs.get('backup', True)
        
        # Create current session data
        current_session = self._create_current_session_data(context)
        
        if len(current_session.conversation_history) <= preserve_recent:
            return f"ℹ️ Session has only {len(current_session.conversation_history)} conversations. No compacting needed."
        
        # Save backup if requested
        if save_backup:
            backup_name = f"backup_before_compact_{int(time.time())}"
            current_session.metadata.name = backup_name
            self.storage.save_session(current_session)
            self.show_info(f"Backup saved as '{backup_name}'", context)
        
        try:
            # Compact session
            compacted_session = await self.compactor.compact_session(
                current_session, instructions, preserve_recent
            )
            
            # Update current context with compacted session
            self._apply_compacted_session(compacted_session, context)
            
            original_count = len(current_session.conversation_history)
            new_count = len(compacted_session.conversation_history)
            
            return f"✅ Session compacted: {original_count} → {new_count} conversations"
            
        except Exception as e:
            return f"❌ Compacting failed: {e}"
    
    def _create_current_session_data(self, context: CommandExecutionContext) -> SessionData:
        """Create session data from current context"""
        now = datetime.now()
        
        metadata = SessionMetadata(
            name="current_session",
            created_at=now,
            last_modified=now,
            description="Current session for compacting",
            project_root=str(context.project_root),
            status=SessionStatus.ACTIVE
        )
        
        conversation_history = getattr(context.smart_ai, 'conversation_history', [])
        
        return SessionData(
            metadata=metadata,
            conversation_history=conversation_history,
            context_data=context.session_data.copy()
        )
    
    def _apply_compacted_session(self, session_data: SessionData, context: CommandExecutionContext):
        """Apply compacted session to current context"""
        if hasattr(context.smart_ai, 'conversation_history'):
            context.smart_ai.conversation_history = session_data.conversation_history


class MemoryCommandHandler(BaseCommandHandler):
    """Handler for /memory command"""
    
    def __init__(self, memory_manager: SessionMemoryManager):
        self.memory_manager = memory_manager
    
    @command_error_handler  
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        action = parsed_cmd.args[0] if parsed_cmd.args else 'show'
        
        if action == 'show':
            return self._show_memory()
        elif action == 'edit':
            return self._edit_memory(parsed_cmd, context)
        elif action == 'save':
            return self._save_memory_entry(parsed_cmd)
        elif action == 'update':
            return self._update_claude_md(context)
        else:
            return f"❌ Unknown memory action: {action}. Available: show, edit, save, update"
    
    def _show_memory(self) -> str:
        """Show current project memory"""
        memory = self.memory_manager.load_project_memory()
        
        if not memory:
            return "No project memory found. Use '/memory update' to initialize."
        
        lines = ["Project Memory:", "=" * 20]
        
        for filename, content in memory.items():
            lines.append(f"\n📄 {filename}")
            lines.append("-" * len(filename))
            # Show first few lines
            content_lines = content.split('\n')
            preview_lines = content_lines[:10]
            for line in preview_lines:
                lines.append(f"  {line}")
            if len(content_lines) > 10:
                lines.append(f"  ... ({len(content_lines) - 10} more lines)")
        
        return "\n".join(lines)
    
    def _edit_memory(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        """Edit memory entry"""
        if len(parsed_cmd.args) < 2:
            return "❌ Usage: /memory edit <filename> [content]"
        
        filename = parsed_cmd.args[1]
        
        if len(parsed_cmd.args) > 2:
            # Content provided directly
            content = " ".join(parsed_cmd.args[2:])
            file_path = self.memory_manager.save_memory_entry(filename, content)
            return f"✅ Memory entry '{filename}' saved to {file_path}"
        else:
            # Interactive edit would go here
            return f"📝 To edit '{filename}', use: /memory edit {filename} <content>"
    
    def _save_memory_entry(self, parsed_cmd: ParsedCommand) -> str:
        """Save memory entry"""
        if len(parsed_cmd.args) < 3:
            return "❌ Usage: /memory save <filename> <content>"
        
        filename = parsed_cmd.args[1]
        content = " ".join(parsed_cmd.args[2:])
        
        file_path = self.memory_manager.save_memory_entry(filename, content)
        return f"✅ Memory entry '{filename}' saved to {file_path}"
    
    def _update_claude_md(self, context: CommandExecutionContext) -> str:
        """Update CLAUDE.md with current session"""
        # Create temporary session data
        current_session = SessionData(
            metadata=SessionMetadata(
                name="current",
                created_at=datetime.now(),
                last_modified=datetime.now(),
                description="Current session for memory update"
            ),
            conversation_history=getattr(context.smart_ai, 'conversation_history', [])
        )
        
        self.memory_manager.update_claude_md(current_session, append=True)
        return f"✅ CLAUDE.md updated with session insights"


class ContextCommandHandler(BaseCommandHandler):
    """Handler for /context command"""
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        action = parsed_cmd.args[0] if parsed_cmd.args else 'show'
        
        if action == 'show':
            return self._show_context(context)
        elif action == 'clear':
            return self._clear_context(context)
        elif action == 'set':
            return self._set_context(parsed_cmd, context)
        else:
            return f"❌ Unknown context action: {action}. Available: show, clear, set"
    
    def _show_context(self, context: CommandExecutionContext) -> str:
        """Show current context"""
        lines = [
            "Current Context:",
            "=" * 20,
            f"Project Root: {context.project_root}",
            f"Current Provider: {context.current_provider}",
            f"Session Data Keys: {list(context.session_data.keys())}",
        ]
        
        # Show conversation stats
        if hasattr(context.smart_ai, 'conversation_history'):
            history = context.smart_ai.conversation_history
            lines.append(f"Conversation Entries: {len(history)}")
            
            if history:
                recent = history[-1]
                lines.append(f"Last Entry: {recent.role} at {recent.timestamp}")
        
        return "\n".join(lines)
    
    def _clear_context(self, context: CommandExecutionContext) -> str:
        """Clear conversation context"""
        if hasattr(context.smart_ai, 'conversation_history'):
            context.smart_ai.conversation_history.clear()
        
        context.session_data.clear()
        context.session_data['session_start'] = time.time()
        
        return "✅ Context cleared"
    
    def _set_context(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        """Set context variable"""
        if len(parsed_cmd.args) < 3:
            return "❌ Usage: /context set <key> <value>"
        
        key = parsed_cmd.args[1]
        value = " ".join(parsed_cmd.args[2:])
        
        context.session_data[key] = value
        return f"✅ Context variable '{key}' set"


class ClearSessionCommandHandler(BaseCommandHandler):
    """Handler for /clear command"""
    
    def __init__(self, storage: SessionStorage, notification_manager: Optional[NotificationManager] = None):
        self.storage = storage
        self.notification_manager = notification_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        save_backup = parsed_cmd.kwargs.get('backup', True)
        force = parsed_cmd.kwargs.get('force', False)
        
        # Count current conversation entries
        current_history = getattr(context.smart_ai, 'conversation_history', [])
        history_count = len(current_history)
        
        if history_count == 0 and not force:
            return "ℹ️ Session is already empty. Use --force to clear session data anyway."
        
        # Save backup if requested and there's content
        if save_backup and history_count > 0:
            backup_name = f"clear_backup_{int(time.time())}"
            
            # Create backup session data
            metadata = SessionMetadata(
                name=backup_name,
                created_at=datetime.now(),
                last_modified=datetime.now(),
                description=f"Backup before clearing session with {history_count} conversations",
                project_root=str(context.project_root),
                status=SessionStatus.ARCHIVED
            )
            
            backup_session = SessionData(
                metadata=metadata,
                conversation_history=current_history,
                context_data=context.session_data.copy()
            )
            
            try:
                self.storage.save_session(backup_session)
                backup_msg = f" (backup saved as '{backup_name}')"
            except Exception as e:
                backup_msg = f" (backup failed: {e})"
        else:
            backup_msg = ""
        
        # Clear conversation history
        if hasattr(context.smart_ai, 'conversation_history'):
            context.smart_ai.conversation_history.clear()
        
        # Clear session data but keep basic info
        context.session_data.clear()
        context.session_data['session_start'] = time.time()
        context.session_data['cleared_at'] = datetime.now().isoformat()
        
        if self.notification_manager:
            self.notification_manager.notify(
                "Session Cleared",
                f"Conversation history cleared{backup_msg}",
                NotificationType.INFO
            )
        
        return f"✅ Session cleared{backup_msg}"


class ResumeCommandHandler(BaseCommandHandler):
    """Handler for /resume command"""
    
    def __init__(self, storage: SessionStorage):
        self.storage = storage
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        # Find most recent session
        sessions = self.storage.list_sessions()
        
        if not sessions:
            return "❌ No sessions found to resume"
        
        # Get most recent session
        recent_session = sessions[0]
        session_name = recent_session['name']
        
        # Check if it's encrypted
        if recent_session['encrypted']:
            return f"❌ Recent session '{session_name}' is encrypted. Use: /load {session_name} --password=<password>"
        
        try:
            session_data = self.storage.load_session(session_name)
            
            # Load session data into context
            context.session_data.clear()
            context.session_data.update(session_data.context_data)
            
            if hasattr(context.smart_ai, 'conversation_history'):
                context.smart_ai.conversation_history = session_data.conversation_history
            
            return f"✅ Resumed session '{session_name}' (last modified: {recent_session['modified'].strftime('%Y-%m-%d %H:%M')})"
            
        except Exception as e:
            return f"❌ Failed to resume session: {e}"


class AutoSaveCommandHandler(BaseCommandHandler):
    """Handler for /autosave command"""
    
    def __init__(self, storage: SessionStorage):
        self.storage = storage
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        action = parsed_cmd.args[0] if parsed_cmd.args else 'status'
        
        if action == 'enable':
            interval = parsed_cmd.kwargs.get('interval', 300)  # 5 minutes default
            return self._enable_autosave(interval, context)
        elif action == 'disable':
            return self._disable_autosave(context)
        elif action == 'status':
            return self._autosave_status(context)
        else:
            return f"❌ Unknown autosave action: {action}. Available: enable, disable, status"
    
    def _enable_autosave(self, interval: int, context: CommandExecutionContext) -> str:
        """Enable autosave with specified interval"""
        # Store autosave settings in session data
        context.session_data['autosave_enabled'] = True
        context.session_data['autosave_interval'] = interval
        context.session_data['autosave_last'] = time.time()
        
        return f"✅ Autosave enabled (interval: {interval} seconds)"
    
    def _disable_autosave(self, context: CommandExecutionContext) -> str:
        """Disable autosave"""
        context.session_data['autosave_enabled'] = False
        return "✅ Autosave disabled"
    
    def _autosave_status(self, context: CommandExecutionContext) -> str:
        """Show autosave status"""
        enabled = context.session_data.get('autosave_enabled', False)
        
        if enabled:
            interval = context.session_data.get('autosave_interval', 300)
            last_save = context.session_data.get('autosave_last', 0)
            next_save = last_save + interval - time.time()
            
            return f"✅ Autosave enabled (interval: {interval}s, next save in: {max(0, int(next_save))}s)"
        else:
            return "❌ Autosave disabled"


# Integration function to register all session commands
def register_session_commands(registry, smart_ai_instance):
    """Register all session management commands with the command registry"""
    
    # Initialize components
    storage = SessionStorage()
    exporter = SessionExporter()
    compactor = SessionCompactor(getattr(smart_ai_instance, 'backend', None))
    memory_manager = SessionMemoryManager()
    notification_manager = getattr(smart_ai_instance, 'notification_manager', None)
    
    # Register /save command
    registry.register(CommandDefinition(
        name="save",
        handler=SaveSessionCommandHandler(storage, notification_manager),
        description="Save current session with conversation history",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("name", str, False, None, "Session name (auto-generated if not provided)"),
            CommandParameter("password", str, False, None, "Password for encryption"),
            CommandParameter("description", str, False, "", "Session description"),
            CommandParameter("compress", bool, False, False, "Enable compression")
        ],
        examples=[
            "/save my_session",
            "/save my_session --password=secret123",
            "/save --description='Bug fixing session' --compress"
        ],
        usage="/save [name] [--password=<pwd>] [--description=<desc>] [--compress]"
    ))
    
    # Register /load command
    registry.register(CommandDefinition(
        name="load",
        handler=LoadSessionCommandHandler(storage, notification_manager),
        description="Load previously saved session",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("name", str, True, None, "Session name to load"),
            CommandParameter("password", str, False, None, "Password for encrypted session"),
            CommandParameter("merge", bool, False, False, "Merge with current session instead of replacing")
        ],
        examples=[
            "/load my_session",
            "/load my_session --password=secret123",
            "/load my_session --merge"
        ],
        usage="/load <name> [--password=<pwd>] [--merge]"
    ))
    
    # Register /sessions command
    registry.register(CommandDefinition(
        name="sessions",
        handler=ListSessionsCommandHandler(storage),
        description="List all available saved sessions",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("verbose", bool, False, False, "Show detailed information"),
            CommandParameter("format", str, False, "table", "Output format", ["table", "json"])
        ],
        examples=[
            "/sessions",
            "/sessions --verbose",
            "/sessions --format=json"
        ],
        usage="/sessions [--verbose] [--format=<format>]"
    ))
    
    # Register /delete command for sessions
    registry.register(CommandDefinition(
        name="delete",
        handler=DeleteSessionCommandHandler(storage, notification_manager),
        description="Delete saved session with confirmation",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("name", str, True, None, "Session name to delete"),
            CommandParameter("force", bool, False, False, "Skip confirmation prompt")
        ],
        examples=[
            "/delete old_session --force"
        ],
        usage="/delete <name> --force"
    ))
    
    # Register /export command
    registry.register(CommandDefinition(
        name="export",
        handler=ExportSessionCommandHandler(storage, exporter),
        description="Export session in various formats (text, json, markdown, html)",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("session", str, False, "current", "Session name or 'current'"),
            CommandParameter("format", str, False, "json", "Export format", ["json", "text", "markdown", "html", "zip"]),
            CommandParameter("output", str, False, None, "Output file path"),
            CommandParameter("metadata", bool, False, True, "Include metadata in export"),
            CommandParameter("password", str, False, None, "Password for encrypted session")
        ],
        examples=[
            "/export current --format=markdown",
            "/export my_session --format=html --output=report.html",
            "/export my_session --format=zip"
        ],
        usage="/export [session] [--format=<fmt>] [--output=<path>] [--metadata] [--password=<pwd>]"
    ))
    
    # Register /import command
    registry.register(CommandDefinition(
        name="import",
        handler=ImportSessionCommandHandler(storage),
        description="Import session from file",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("file", str, True, None, "File path to import"),
            CommandParameter("name", str, False, None, "New session name"),
            CommandParameter("merge", bool, False, False, "Merge with current session")
        ],
        examples=[
            "/import session_backup.json",
            "/import session_backup.json --name=restored_session",
            "/import session_backup.json --merge"
        ],
        usage="/import <file> [--name=<name>] [--merge]"
    ))
    
    # Register /compact command
    registry.register(CommandDefinition(
        name="compact",
        handler=CompactSessionCommandHandler(compactor, storage),
        description="Compact conversation with optional focus instructions",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("instructions", str, False, None, "Focus instructions for compacting"),
            CommandParameter("keep", int, False, 10, "Number of recent conversations to preserve"),
            CommandParameter("backup", bool, False, True, "Create backup before compacting")
        ],
        examples=[
            "/compact",
            "/compact focus on technical decisions --keep=15",
            "/compact summarize key points --backup=false"
        ],
        usage="/compact [instructions] [--keep=<num>] [--backup]"
    ))
    
    # Register /memory command
    registry.register(CommandDefinition(
        name="memory",
        handler=MemoryCommandHandler(memory_manager),
        description="Edit project memory (CLAUDE.md style)",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("action", str, False, "show", "Memory action", ["show", "edit", "save", "update"]),
            CommandParameter("filename", str, False, None, "Memory file name for edit/save"),
            CommandParameter("content", str, False, None, "Content for edit/save")
        ],
        examples=[
            "/memory show",
            "/memory edit preferences 'Use TypeScript for all new components'",
            "/memory update"
        ],
        usage="/memory [action] [filename] [content]"
    ))
    
    # Register /context command
    registry.register(CommandDefinition(
        name="context",
        handler=ContextCommandHandler(),
        description="Manage conversation context and history",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("action", str, False, "show", "Context action", ["show", "clear", "set"]),
            CommandParameter("key", str, False, None, "Context variable key for set action"),
            CommandParameter("value", str, False, None, "Context variable value for set action")
        ],
        examples=[
            "/context show",
            "/context clear",
            "/context set project_type 'React TypeScript'"
        ],
        usage="/context [action] [key] [value]"
    ))
    
    # Register /clear command
    registry.register(CommandDefinition(
        name="clear",
        handler=ClearSessionCommandHandler(storage, notification_manager),
        description="Clear current session conversation history",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("backup", bool, False, True, "Create backup before clearing"),
            CommandParameter("force", bool, False, False, "Force clear even if session is empty")
        ],
        examples=[
            "/clear",
            "/clear --backup=false",
            "/clear --force"
        ],
        usage="/clear [--backup] [--force]"
    ))
    
    # Register /resume command
    registry.register(CommandDefinition(
        name="resume",
        handler=ResumeCommandHandler(storage),
        description="Resume interrupted sessions",
        category=CommandCategory.SESSION,
        examples=["/resume"],
        usage="/resume"
    ))
    
    # Register /autosave command
    registry.register(CommandDefinition(
        name="autosave",
        handler=AutoSaveCommandHandler(storage),
        description="Configure automatic session saving",
        category=CommandCategory.SESSION,
        parameters=[
            CommandParameter("action", str, False, "status", "Autosave action", ["enable", "disable", "status"]),
            CommandParameter("interval", int, False, 300, "Autosave interval in seconds")
        ],
        examples=[
            "/autosave enable --interval=600",
            "/autosave disable",
            "/autosave status"
        ],
        usage="/autosave [action] [--interval=<seconds>]"
    ))


if __name__ == "__main__":
    # Example usage and testing
    import tempfile
    import uuid
    
    print("Smart AI Session Management Commands")
    print("=" * 50)
    
    # Create test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = SessionStorage(Path(temp_dir))
        exporter = SessionExporter()
        
        # Create test session data
        now = datetime.now()
        metadata = SessionMetadata(
            name="test_session",
            created_at=now,
            last_modified=now,
            description="Test session for development",
            tags=["test", "development"]
        )
        
        conversation_history = [
            ConversationEntry(
                id=str(uuid.uuid4()),
                timestamp=now,
                role="user",
                content="Hello, how are you?",
                provider="claude"
            ),
            ConversationEntry(
                id=str(uuid.uuid4()),
                timestamp=now,
                role="assistant", 
                content="I'm doing well, thank you! How can I help you today?",
                provider="claude"
            )
        ]
        
        session_data = SessionData(
            metadata=metadata,
            conversation_history=conversation_history,
            context_data={"test_key": "test_value"}
        )
        
        # Test storage
        print("1. Testing session storage...")
        saved_path = storage.save_session(session_data)
        print(f"   Saved to: {saved_path}")
        
        loaded_session = storage.load_session("test_session")
        print(f"   Loaded session: {loaded_session.metadata.name}")
        print(f"   Conversations: {len(loaded_session.conversation_history)}")
        
        # Test export
        print("\n2. Testing session export...")
        export_path = Path(temp_dir) / "export_test.md"
        exported = exporter.export_session(session_data, ExportFormat.MARKDOWN, export_path)
        print(f"   Exported to: {exported}")
        
        # Show exported content
        print(f"   Preview:\n{exported.read_text()[:200]}...")
        
        # Test encryption if available
        if ENCRYPTION_AVAILABLE:
            print("\n3. Testing encryption...")
            encrypted_path = storage.save_session(session_data, password="test123")
            print(f"   Encrypted session saved to: {encrypted_path}")
            
            decrypted_session = storage.load_session("test_session", password="test123")
            print(f"   Successfully decrypted session: {decrypted_session.metadata.name}")
        else:
            print("\n3. Encryption not available (install cryptography package)")
        
        print("\n✅ All tests completed successfully!")