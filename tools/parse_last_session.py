import json

path = r"C:\Users\HiTech\.gemini\antigravity-ide\brain\ddd66468-ca7d-413f-b756-7c73f07e95f9\.system_generated\logs\transcript.jsonl"
with open("tools/last_session_prompts.txt", "w", encoding="utf-8") as out:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if data.get("type") == "USER_INPUT":
                out.write(f"=== STEP {data.get('step_index')} ===\n")
                out.write(data.get("content", "") + "\n\n")
print("Done writing last_session_prompts.txt")
