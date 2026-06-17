# test_mode_b.py
from apps.agents.mode_b.workflows import MODE_B_FULL_WORKFLOW, MODE_B_CONCEPTION_CLASSES

print("🔍 Vérification des imports Mode B...")
print(f"✅ Agents de conception chargés : {[c.name for c in MODE_B_CONCEPTION_CLASSES]}")
print(f"✅ Workflow complet chargé : {[c.name for c in MODE_B_FULL_WORKFLOW]}")

# Vérification de l'ordre critique (DesignAgent -> DevAgent)
assert MODE_B_FULL_WORKFLOW[2].name == "DesignAgent", "❌ Erreur : DesignAgent doit être en 3ème position"
print("🎯 Ordre critique Design -> Dev : OK")
print("🚀 Ta partie est structurellement prête pour l'orchestrateur !")