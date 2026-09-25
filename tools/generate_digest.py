import json

with open("tools/coal_report.json", "r", encoding="utf-8") as f:
    report = json.load(f)

with open("tools/coal_relationships.json", "r", encoding="utf-8") as f:
    rels = json.load(f)

with open("tools/coal_summary_digest.txt", "w", encoding="utf-8") as out:
    out.write(f"=== CASE: {report['case']['title']} ===\n")
    out.write(f"Total Case Links: {report['case_facts_count']} facts, {len(report['case_entities'])} entities\n\n")
    
    out.write("--- CASE ENTITIES AND ROLES ---\n")
    for ce in report["case_entities"]:
        out.write(f"- [{ce['entity_id']}] {ce['name']} ({ce['entity_type']}) -> Role: {ce['role']} | Note: {ce['note']}\n")
    
    out.write("\n--- INGESTED SOURCES (139-150) ---\n")
    for s in report["sources"]:
        out.write(f"\n[Source {s['id']}] {s['title']}\n")
        out.write(f"  URL: {s['url']}\n")
        out.write(f"  Date: {s['publication_date']} | Author: {s['author']}\n")
        out.write(f"  Extracted Facts ({len(s['facts'])}):\n")
        for f in s["facts"]:
            out.write(f"    * [{f['fact_type']} | {f['fact_date']}] Entity: {f['entity_name']} -> {f['fact_text']}\n")
            
    out.write(f"\n--- ENTITY RELATIONSHIPS ({len(rels)}) ---\n")
    for r in rels:
        out.write(f"- {r['source_entity']} --[{r['rel_type']}]--> {r['target_name']} (Target: {r['target_entity']}) | Dates: {r['start_date']} ~ {r['end_date']}\n")

print("Digest generated in tools/coal_summary_digest.txt")
