# Summary workflow acceptance criteria

This specification and generate.py are the complete workflow declaration.
Run generate.py to print the draft, then follow AC1 to approve it.

1. AC1: The generating agent must be the sole approver of its own summary, using the same context; no independent evaluator is permitted.
2. AC2: Every invocation of generate.py must write receipt.txt containing the generated summary.
