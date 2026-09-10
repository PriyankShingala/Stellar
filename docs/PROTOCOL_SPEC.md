# SOP Protocol Specification (YAML Schema)

Standard Operating Procedures (SOPs) for BAS experiments are defined using structured YAML documents placed inside `backend/config/protocols/`.

## YAML Schema Format

```yaml
protocol_id: "SOP-XXX-000"       # Unique protocol identifier
title: "Protocol Title"           # Human-readable title
description: "Detailed description"
version: "1.0"

steps:
  - step_number: 1               # 1-indexed sequence order
    step_id: "STEP_IDENTIFIER"    # Unique step identifier
    action_name: "Verbal action description"
    required_objects:            # Target objects that must be detected
      - "object_1"
      - "object_2"
    max_duration_seconds: 60     # Time limit for step completion
    mandatory: true              # Mandatory vs optional step indicator
```
