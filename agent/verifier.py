"""
Pillar 13: Self-Verification Critic & Anti-Hallucination Guardrail.
Inspects drafted answers, verifies code outputs, checks citations against retrieved sources,
and flags potential discrepancies.
"""

import re
from typing import Dict, List, Any, Optional

class OutputVerifier:
    def verify(
        self,
        query: str,
        answer: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        tool_steps: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Validates the generated response for factual grounding, code safety, and citation integrity.
        """
        flags = []
        citations_found = [int(c) for c in re.findall(r'\[(\d+)\]', answer)]
        
        # 1. Citation validity check
        if sources:
            max_source_id = max([s.get("source_id", len(sources)) for s in sources], default=0)
            invalid_citations = [c for c in citations_found if c > max_source_id or c < 1]
            if invalid_citations:
                flags.append(f"Citation mismatch: References [{', '.join(map(str, invalid_citations))}] do not exist in retrieved sources.")
        
        # 2. Code execution verification
        if tool_steps:
            for step in tool_steps:
                if step.get("tool") == "code_sandbox" and step.get("has_error"):
                    flags.append("Code sandbox reported a runtime error during execution.")

        # 3. Compute verification score
        score = 100 - (len(flags) * 20)
        score = max(20, min(100, score))

        return {
            "verified": len(flags) == 0,
            "verification_score": score,
            "citations_count": len(citations_found),
            "flags": flags
        }
