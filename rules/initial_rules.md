# Initial Fraud Rules

## Rule 1: Duplicate ID
- If the same invoice/claim ID appears more than once in a short period → Flag as fraud
- Threshold: Same ID within 30 days

## Rule 2: High Amount
- If amount > $10,000 → Suspicious
- Threshold: Configurable

## Rule 3: Frequency Spike
- If same user submits > 5 claims in 7 days → Flag
- Threshold: 5 claims per week

## Rule 4: Pattern Mismatch
- If billing address doesn't match user history → Alert
- Logic: Compare against known patterns

## Rule 5: Unusual Timing
- Claims submitted outside normal business hours → Low risk flag
- Hours: 9 AM - 5 PM

## Rule 6: Round Number Amounts
- Amounts ending in multiple zeros (e.g., $5000.00) → Potential fabrication
- Threshold: Amounts divisible by 1000

## Rule 7: Same Provider Multiple Claims
- If one provider handles > 50% of user's claims → Investigate
- Threshold: 50%

## Rule 8: Age Mismatch
- If claimed service date is in future → Invalid
- Logic: Date validation

## Rule 9: Location Anomaly
- Claims from unusual locations for user → Flag
- Based on user history

## Rule 10: Amount Deviation
- If amount deviates > 200% from user's average → Alert
- Threshold: 200%