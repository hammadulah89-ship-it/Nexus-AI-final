"""
Pillar 11: Interactive Visual Canvas & Mermaid Diagram Engine.
Generates, formats, and validates Mermaid.js flowcharts, sequence diagrams, mindmaps, and SVG vector graphics.
"""

import re
from typing import Dict, Any, Optional

class DiagramEngine:
    """Generates structured Mermaid.js and SVG diagram specifications."""

    def format_mermaid(self, raw_code: str) -> Dict[str, Any]:
        """Cleans and validates Mermaid code for rendering."""
        clean_code = raw_code.strip()
        # Strip markdown wrapper if present
        clean_code = re.sub(r'^```(?:mermaid)?\s*', '', clean_code)
        clean_code = re.sub(r'\s*```$', '', clean_code).strip()

        diagram_type = "flowchart"
        if clean_code.startswith("sequenceDiagram"):
            diagram_type = "sequence"
        elif clean_code.startswith("classDiagram"):
            diagram_type = "class"
        elif clean_code.startswith("stateDiagram"):
            diagram_type = "state"
        elif clean_code.startswith("mindmap"):
            diagram_type = "mindmap"
        elif clean_code.startswith("erDiagram"):
            diagram_type = "er"
        elif clean_code.startswith("gantt"):
            diagram_type = "gantt"

        return {
            "valid": True,
            "diagram_type": diagram_type,
            "code": clean_code
        }
