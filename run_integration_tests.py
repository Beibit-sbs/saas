#!/usr/bin/env python3
"""Run domain integration tests and report results."""
import subprocess
import sys
import os

# Set environment
os.chdir("/home/sbs/AI/infra")
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"

# Run the tests
cmd = [
    "docker", "compose",
    "--env-file", ".env",
    "run", "--rm", 
    "backend-tests",
    "pytest",
    "tests/test_domain_module_db_integration.py",
    "-m", "integration",
    "-v",
    "--tb=short",
    "--no-cov",
]

print(f"Running: {' '.join(cmd)}")
print("=" * 80)
sys.stdout.flush()

result = subprocess.run(cmd, env=env)
sys.exit(result.returncode)
