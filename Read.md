# Open Fraud Intelligence Platform (OFIP)

## Overview

OFIP is a global open fraud intelligence framework with controlled governance. It's a universal platform for fraud detection across any domain, combining open-source collaboration with structured oversight.

## How It Works

OFIP processes inputs through a simple rule-based engine to detect potential fraud.

### Input
- Documents (invoices, claims, transactions) in JSON or text format

### Processing
1. Parse input data
2. Apply fraud detection rules
3. Calculate risk score
4. Generate alerts

### Example Output
```
ID: INV001, Risk Score: 70
Alerts: ['Duplicate invoice detected', 'Frequency spike detected']
```

Run `python demo.py` to see the system in action with sample data.

## Project Structure

### 🔓 Open Core (Public)
- Framework and plugin system
- Basic rule engine
- Sample datasets

*Purpose*: Attract contributors and build a robust ecosystem.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Explore the codebase in `api/`, `core/`, `ocr/`, `plugins/`
4. Check for "good first issues" in GitHub Issues

## How to Contribute

We welcome contributions! Follow these guidelines:

- **No direct commits**: All changes must go through Pull Requests (PRs)
- **Mandatory review**: Every PR requires review and approval
- **Plugin isolation**: Contributions should be modular and isolated
- **Code standards**: Follow the project's coding guidelines (TBD in contributing docs)

### Contribution Process
1. Create a feature branch from `main`
2. Make your changes
3. Submit a PR with a clear description
4. Wait for review and feedback

## Community Roles

- **Public Contributors**: Submit plugins, fix bugs, suggest features
- **Trusted Contributors**: Review PRs, help maintain quality
- **Core Maintainers**: Final authority on merges and roadmap

## Community Strategy

We're building a community of contributors → maintainers → ecosystem leaders.

- **Stage 1**: Focus on onboarding with clear issues and documentation
- **Stage 2**: Add domain-specific plugins (medical, finance, invoice)
- **Stage 3**: Establish as a recognized open project

Join us on GitHub Discussions, LinkedIn, and Reddit to connect and contribute!

## Governance

- All changes via PR with review
- Core maintainers control merges and direction
- Security-first: Code is reviewed for safety
- Plugin system ensures modularity and safety

---

*Help us build the global standard for fraud detection systems.*