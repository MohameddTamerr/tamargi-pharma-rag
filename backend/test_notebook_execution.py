import json
import os
import sys
import time

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

notebook_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Tamargi_RAG_V2_Research.ipynb"))

print(f"Loading notebook: {notebook_path}")
with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

global_scope = {}
local_scope = {}

print("=" * 80)
print("EXECUTING ALL CODE CELLS IN Tamargi_RAG_V2_Research.ipynb...")
print("=" * 80)

code_cell_idx = 0
for idx, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        code_cell_idx += 1
        code_src = "".join(cell["source"])
        print(f"\n--- [Executing Code Cell {code_cell_idx}] ---")
        # Filter out display() calls or mock display for terminal testing
        def mock_display(obj):
            print(f"[Display output table]:\n{obj}")
        global_scope["display"] = mock_display
        
        t0 = time.time()
        try:
            exec(code_src, global_scope, global_scope)
            t1 = time.time()
            print(f"[Cell {code_cell_idx} PASSED in {t1-t0:.2f}s]")
        except Exception as e:
            print(f"[Cell {code_cell_idx} FAILED]: {e}")
            raise e

print("\n" + "=" * 80)
print("ALL NOTEBOOK CELLS EXECUTED SUCCESSFULLY WITHOUT ERRORS (100%)")
print("=" * 80)
