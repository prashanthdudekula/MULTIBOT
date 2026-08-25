#!/usr/bin/env python3
"""
Root-level launcher — delegates to magicpin-ai-challenge/judge_simulator.py
so you can just run:  python judge_simulator.py
"""
import subprocess
import sys
import os

sim = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "magicpin-ai-challenge", "judge_simulator.py")
result = subprocess.run([sys.executable, sim] + sys.argv[1:])
sys.exit(result.returncode)
