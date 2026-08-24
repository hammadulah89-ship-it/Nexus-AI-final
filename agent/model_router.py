"""
Pillar 9: Multi-Model Brain Router.
Dynamically routes user tasks to specialized NexusAI engines based on task complexity, coding needs, or speed.
"""

from typing import Dict, Any, Tuple, Optional

# Engine display mapping
ENGINE_REGISTRY = {
    "openai/gpt-oss-120b": {
        "engine_name": "NexusAI Ultra",
        "description": "Flagship 120B reasoning, deep research, and multi-step logic core.",
        "best_for": ["deep_research", "math_engine", "rag_search", "reasoning", "complex_logic"]
    },
    "qwen/qwen3.6-27b": {
        "engine_name": "NexusAI Code Specialist",
        "description": "Specialized programming, script generation, and algorithm core.",
        "best_for": ["code_sandbox", "coding", "python", "algorithms", "data_analysis"]
    },
    "groq/compound": {
        "engine_name": "NexusAI Turbo",
        "description": "Ultra-fast low-latency classification and instant responses.",
        "best_for": ["direct_chat", "memory_save", "memory_recall", "quick_answers"]
    }
}

class MultiModelRouter:
    def route_task(self, query: str, intent: str, requested_model: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Selects the optimal model for the given task and intent.
        Returns: (model_id: str, engine_display_name: str, reason: str)
        """
        # User requested specific engine
        if requested_model and requested_model in ENGINE_REGISTRY:
            engine_info = ENGINE_REGISTRY[requested_model]
            return requested_model, engine_info["engine_name"], f"Selected: {engine_info['engine_name']}"

        q_lower = query.lower()

        # 1. Coding & Python Sandbox -> NexusAI Code Specialist
        if intent == "code_sandbox" or any(w in q_lower for w in ["python", "code", "function", "script", "algorithm", "debug", "refactor"]):
            return "qwen/qwen3.6-27b", "NexusAI Code Specialist", "Routed to NexusAI Code Engine for programming"

        # 2. Deep Research / Complex Multi-hop / Math / Document RAG -> NexusAI Ultra
        if intent in ("deep_research", "math_engine", "rag_search") or len(query.split()) > 25:
            return "openai/gpt-oss-120b", "NexusAI Ultra", "Routed to NexusAI Ultra for deep reasoning"

        # 3. Standard queries -> NexusAI Ultra flagship
        return "openai/gpt-oss-120b", "NexusAI Ultra", "Routed to NexusAI flagship core"
