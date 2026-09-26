from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class FrameSnapshot:
    timestamp_utc: str
    analysis: Dict[str, Any]


@dataclass
class VisionSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    started_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    frames: List[FrameSnapshot] = field(default_factory=list)
    max_frames: int = 8

    def append(self, analysis: Dict[str, Any]) -> None:
        self.frames.append(
            FrameSnapshot(
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                analysis=analysis,
            )
        )
        if len(self.frames) > self.max_frames:
            self.frames = self.frames[-self.max_frames:]

    def previous_analysis(self) -> Optional[Dict[str, Any]]:
        if not self.frames:
            return None
        return self.frames[-1].analysis

    def compact_context(self) -> List[Dict[str, Any]]:
        compact = []
        for frame in self.frames[-4:]:
            a = frame.analysis or {}
            compact.append({
                "timestamp_utc": frame.timestamp_utc,
                "outfit": a.get("outfit", {}),
                "scores": a.get("scores", {}),
                "observations": a.get("observations", [])[:4],
                "adjustments": a.get("adjustments", [])[:4],
            })
        return compact


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, VisionSession] = {}

    def create(self) -> VisionSession:
        session = VisionSession()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[VisionSession]:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None


store = SessionStore()
