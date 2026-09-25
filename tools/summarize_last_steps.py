import json

path = r"C:\Users\HiTech\.gemini\antigravity-ide\brain\ddd66468-ca7d-413f-b756-7c73f07e95f9\.system_generated\logs\transcript.jsonl"
with open("tools/last_session_summary.txt", "w", encoding="utf-8") as out:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            idx = data.get("step_index", 0)
            if idx >= 750:
                content = str(data.get("content", ""))[:120].replace("\n", " ")
                out.write(f"[{idx}] {data.get('type')}: {content}\n")
                if data.get("tool_calls"):
                    for tc in data["tool_calls"]:
                        out.write(f"   TOOL: {tc.get('name')} {list(tc.get('args', {}).keys())}\n")
print("Done writing summary")
