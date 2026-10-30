import re
import sys
from pathlib import Path

# Add project root to path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from pmbok.audit.audit_validator import PMBOKAuditValidator

def run_regex_regression():
    """Permanent regression test for placeholder detection regex."""
    patterns = PMBOKAuditValidator.PLACEHOLDER_PATTERNS
    
    test_cases = [
        # --- CATEGORY: Legitimate Currency (Should NOT match) ---
        ("$1,000", False),
        ("$50k", False),
        ("$2.5M", False),
        ("$0", False),
        ("USD 1,000", False),
        ("$1,000.00", False),
        ("The cost is $1,000 and we expect high compliance.", False),
        ("$", False), # Lone dollar sign
        
        # --- CATEGORY: Valid Placeholders (Should match) ---
        ("$[amount]", True),
        ("$[1000]", True),
        ("$[ ]", True),
        ("The total is $[TBD]", True),
        ("TBD", True),
        ("To Be Determined", True),
        ("FIXME", True),
        ("[DRAFT]", True),
        ("xxx", True),
        ("###", True),
        ("~~~", True),
        
        # --- CATEGORY: Edge Cases ---
        ("$[]", False), # Empty brackets currently don't match [^\]]+
    ]
    
    print(f"ADPA Regex Regression Test Suite")
    print(f"Validator Class: {PMBOKAuditValidator.__name__}")
    print("-" * 60)
    print(f"{'Input String':<40} | {'Expected':<8} | {'Status':<6}")
    print("-" * 60)
    
    failures = 0
    for text, expected_match in test_cases:
        actual_match = False
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                actual_match = True
                break
        
        status = "✅ OK" if actual_match == expected_match else "❌ FAIL"
        if actual_match != expected_match:
            failures += 1
            
        print(f"{text:<40} | {str(expected_match):<8} | {status:<6}")
    
    print("-" * 60)
    if failures == 0:
        print(f"RESULT: SUCCESS ({len(test_cases)} tests passed)")
        sys.exit(0)
    else:
        print(f"RESULT: FAILED ({failures} tests failed)")
        sys.exit(1)

if __name__ == "__main__":
    run_regex_regression()
