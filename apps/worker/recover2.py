import json
import re
import os

log_path = r"C:\Users\subhankar nath\.gemini\antigravity\brain\d8cd61ed-c222-4233-a3b2-dd565646a75b\.system_generated\logs\overview.txt"
with open(log_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

output = {}

for line in lines:
    try:
        data = json.loads(line)
        if data.get("type") == "TOOL_RESPONSE":
            for call in data.get("tool_calls", []):
                if call.get("name") == "view_file":
                    content = call.get("response", {}).get("output", "")
                    if "process_contract.py" in content and "1:" in content:
                        for line_content in content.split("\n"):
                            match = re.match(r"^(\d+):\s(.*)$", line_content)
                            if match:
                                line_num = int(match.group(1))
                                line_text = match.group(2)
                                output[line_num] = line_text
    except Exception as e:
        pass

if output:
    print(f"Recovered {len(output)} lines from view_file")
    with open(r"C:\Users\subhankar nath\Desktop\Legal-Tech\apps\worker\recovered_lines.py", "w", encoding="utf-8") as f:
        for i in range(1, max(output.keys()) + 1):
            f.write(output.get(i, f"# MISSING LINE {i}") + "\n")
else:
    print("No lines recovered")
