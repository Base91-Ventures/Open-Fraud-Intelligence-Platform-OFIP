"""
Basic Rule Engine for Fraud Detection
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod


class Rule(ABC):
    @abstractmethod
    def evaluate(self, data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass


class RuleEngine:
    def __init__(self):
        self.rules: List[Rule] = []

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def evaluate_all(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for rule in self.rules:
            if rule.evaluate(data):
                results.append({
                    "rule": rule.__class__.__name__,
                    "description": rule.get_description(),
                    "triggered": True
                })
        return results


# Example rule
class SuspiciousAmountRule(Rule):
    def __init__(self, threshold: float = 10000.0):
        self.threshold = threshold

    def evaluate(self, data: Dict[str, Any]) -> bool:
        return data.get("amount", 0) > self.threshold

    def get_description(self) -> str:
        return f"Transaction amount exceeds {self.threshold}"