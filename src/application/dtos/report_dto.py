"""
Report DTO

This module defines the ReportDTO (Data Transfer Object) for transferring report data
between layers of the application.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class ReportDTO:
    """Data Transfer Object for report data."""

    report_type: str
    content: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    time_period: Optional[str] = None
    view_id: Optional[int] = None
    view_name: Optional[str] = None
    view_ids: Optional[List[int]] = None
    limit: Optional[int] = None
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary.

        Returns:
            Dictionary representation
        """
        # Convert to dict using dataclasses.asdict
        result = asdict(self)

        # Handle datetime objects
        result['generated_at'] = self.generated_at.isoformat() if self.generated_at else None

        # For large reports, we might want to truncate the content
        if len(self.content) > 1000:
            preview = self.content[:1000] + "... [content truncated]"
            result['content_preview'] = preview

        return result
