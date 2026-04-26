# System Flow

## Overview
OFIP processes inputs through a simple rule-based engine to detect potential fraud.

## Input
- Documents (invoices, claims, transactions) in JSON or text format
- Example: Invoice data with ID, amount, date, user info

## Processing
1. Parse input data
2. Apply fraud detection rules
3. Calculate risk score
4. Generate alerts

## Output
- Risk score (0-100)
- List of triggered alerts with explanations
- Example:
  ```
  Risk Score: 85
  Alerts:
  - Duplicate invoice detected
  - Amount unusually high
  ```