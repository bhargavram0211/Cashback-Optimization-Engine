# Utility Scripts

This directory contains utility scripts for development, testing, and maintenance.

## Available Scripts

### `audit_mappings.py`

Analyzes the coverage of the `NormalizationMapper` against all Plaid PFCv2 categories.

**Purpose:**
- Verify mapping coverage
- Identify gaps in category mappings
- Show distribution across reward buckets
- Find categories using primary fallbacks

**Usage:**
```bash
python scripts/audit_mappings.py
```

**Output:**
- Summary statistics for each reward bucket
- List of categories falling back to GENERAL (Tier 3)
- List of categories using Primary fallback (Tier 2)
- Coverage analysis and recommendations

**Example Output:**
```
Total categories: 123
Coverage (non-GENERAL): 32.5%
  - Tier 1 (Detailed):  23 categories (18.7%)
  - Tier 2 (Primary):   17 categories (13.8%)
  - Tier 3 (General):   83 categories (67.5%)
```

**When to Run:**
- After modifying mapper logic
- After adding new category mappings
- Before deploying changes to production
- When debugging category classification issues

---

## Adding New Scripts

When adding new scripts to this directory:

1. **Use a descriptive name**: `verb_noun.py` (e.g., `analyze_transactions.py`)
2. **Add shebang**: `#!/usr/bin/env python3` at the top
3. **Add docstring**: Describe purpose, usage, and output
4. **Make executable**: `chmod +x scripts/your_script.py`
5. **Update this README**: Document the new script
6. **Add to .gitignore**: If it generates temporary files

## Best Practices

- **Standalone scripts**: Scripts should be runnable without running the full application
- **Clear output**: Use emojis and formatting for readability
- **Error handling**: Handle missing files and errors gracefully
- **Documentation**: Include usage examples in docstrings
- **Dependencies**: Only use dependencies from `requirements.txt`

