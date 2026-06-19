"""Vérifie la structure du pipeline Mode B."""

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")
django.setup()

from apps.agents.mode_b import MODE_B_AGENT_CLASSES, MODE_B_CONCEPTION_CLASSES

print("Verification des imports Mode B...")
print(f"Agents conception : {[c.name for c in MODE_B_CONCEPTION_CLASSES]}")
print(f"Pipeline complet  : {[c.name for c in MODE_B_AGENT_CLASSES]}")

assert MODE_B_AGENT_CLASSES[2].name == "DesignAgent"
assert MODE_B_AGENT_CLASSES[3].name == "DevAgent"
print("Ordre Design -> Dev : OK")
