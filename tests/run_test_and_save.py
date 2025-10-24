"""
Run PostHog test and save output to file.
Works around terminal output issues.
"""

import sys
import subprocess
from datetime import datetime

output_file = "test_results_output.txt"

print(f"Running test and saving to {output_file}...")

with open(output_file, "w") as f:
    f.write(f"LipService Test Run - {datetime.now()}\n")
    f.write("=" * 80 + "\n\n")
    
    # Step 1: Generate logs
    f.write("STEP 1: Generating realistic PostHog-style logs...\n")
    f.write("-" * 80 + "\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "tests/integration/generate_posthog_style_logs.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        f.write(result.stdout)
        if result.stderr:
            f.write("STDERR:\n" + result.stderr)
        f.write("\n")
    except Exception as e:
        f.write(f"Error generating logs: {e}\n\n")
    
    # Step 2: Run test
    f.write("\nSTEP 2: Running test with generated logs...\n")
    f.write("-" * 80 + "\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "tests/integration/test_with_generated_logs.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        f.write(result.stdout)
        if result.stderr:
            f.write("STDERR:\n" + result.stderr)
        f.write("\n")
    except Exception as e:
        f.write(f"Error running test: {e}\n\n")
    
    f.write("\n" + "=" * 80 + "\n")
    f.write("Test complete! Check results above.\n")

print(f"Done! Results saved to {output_file}")
print("Opening file...")

