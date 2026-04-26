"""
Example Plugin for OFIP
"""

from core.plugin_manager import Plugin
from typing import Dict, Any


class ExamplePlugin(Plugin):
    def get_name(self) -> str:
        return "example"

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Example processing: add a flag if amount is suspicious
        if data.get("amount", 0) > 5000:
            data["suspicious_flag"] = True
        else:
            data["suspicious_flag"] = False
        return data