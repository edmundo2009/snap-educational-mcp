import json
from mcp_server.parsers.math_parser import parse_math_problem
from mcp_server.tools.block_generator import SnapBlockGenerator

# Initialize generator
gen = SnapBlockGenerator(
    "mcp_server/knowledge/snap_blocks.json",
    "mcp_server/knowledge/patterns.json"
)

# Test simplest possible problem
problem = "If 7 hours to mow 4 lawns, how many in 35 hours?"
parsed = parse_math_problem(problem)
result = gen.generate_from_math_pattern(parsed)

# Print the actual opcodes being sent
blocks = result["payload"]["scripts"][0]["blocks"]
print("\n=== OPCODES BEING SENT ===")
for b in blocks:
    print(f"  - {b['opcode']} (category: {b['category']})")

# Save to file for manual inspection
with open("debug_output.json", "w") as f:
    json.dump(result, f, indent=2)

print("\n✅ Saved to debug_output.json")
print("Copy this JSON and manually paste into Snap! console to see what errors you get")
