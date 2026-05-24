import json
import re

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
                    if "File Path: `file:///C:/Users/subhankar%20nath/Desktop/Legal-Tech/apps/worker/tasks/process_contract.py`" in content:
                        # Extract lines
                        # Format is <line_number>: <original_line>
                        for line_content in content.split("\n"):
                            match = re.match(r"^(\d+):\s(.*)$", line_content)
                            if match:
                                line_num = int(match.group(1))
                                line_text = match.group(2)
                                if line_num not in output:
                                    output[line_num] = line_text
    except:
        pass

# Also get replace_file_content calls to get the latest state
for line in lines:
    try:
        data = json.loads(line)
        if data.get("type") == "TOOL_RESPONSE":
            for call in data.get("tool_calls", []):
                if call.get("name") == "multi_replace_file_content" or call.get("name") == "replace_file_content":
                    content = call.get("response", {}).get("output", "")
                    if "process_contract.py" in content:
                        print("Found replace call")
                        # I won't parse diffs automatically, I will just dump the output keys to see if we have lines
    except:
        pass

with open(r"C:\Users\subhankar nath\Desktop\Legal-Tech\apps\worker\recovered_lines.txt", "w", encoding="utf-8") as f:
    for i in sorted(output.keys()):
        f.write(f"{i}: {output[i]}\n")
print(f"Recovered {len(output)} lines")
