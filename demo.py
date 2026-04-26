import json
import os

class FraudDetector:
    def __init__(self):
        self.rules = self.load_rules()
        self.data = []

    def load_rules(self):
        # Simple hardcoded rules for demo
        return {
            "duplicate_id": lambda item, data: any(d['id'] == item['id'] for d in data if d != item),
            "high_amount": lambda item, data: item['amount'] > 10000,
            "frequency_spike": lambda item, data: sum(1 for d in data if d['user'] == item['user']) > 5
        }

    def load_data(self, filepath):
        with open(filepath, 'r') as f:
            self.data = json.load(f)

    def detect_fraud(self, item):
        alerts = []
        risk_score = 0

        if self.rules["duplicate_id"](item, self.data):
            alerts.append("Duplicate invoice detected")
            risk_score += 50

        if self.rules["high_amount"](item, self.data):
            alerts.append("Amount unusually high")
            risk_score += 30

        if self.rules["frequency_spike"](item, self.data):
            alerts.append("Frequency spike detected")
            risk_score += 20

        return risk_score, alerts

    def process_all(self):
        results = []
        for item in self.data:
            score, alerts = self.detect_fraud(item)
            results.append({
                "id": item["id"],
                "risk_score": min(score, 100),
                "alerts": alerts
            })
        return results

if __name__ == "__main__":
    detector = FraudDetector()
    detector.load_data("data/sample_data/invoices.json")
    results = detector.process_all()
    for result in results:
        print(f"ID: {result['id']}, Risk Score: {result['risk_score']}")
        if result['alerts']:
            print("Alerts:", result['alerts'])
        print("---")