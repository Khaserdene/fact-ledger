"""Үнэний Бүртгэл — Суурийг цэгцлэх, давхардлыг арилгах, фактуудыг стандартжуулах скрипт.

1. Test entity устгах (ID 2).
2. Давхардсан 12 субъектийг нэгтгэх (Merge).
3. Буруу бичигдсэн нэрийг засах (ID 29: Раднаасумбэрэлийн Гончигдорж).
4. Хоосон fact_id-уудад 'F{id}' оноох.
5. Субъектуудын албан тушаал, гишүүнчлэлийн ирмэгүүдээс суурь он цагийн (chronological) баримтуудыг үүсгэх.
6. Дурдлагуудыг (mentions) шинэчлэн холбох.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path(__file__).resolve().parent.parent / "profiling_facts.db"

def run_cleanup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print(f"Connecting to database: {DB_PATH}")

    # 1. DELETE TEST ENTITY (ID 2)
    c.execute("DELETE FROM facts WHERE entity_id = 2")
    c.execute("DELETE FROM entity_aliases WHERE entity_id = 2")
    c.execute("DELETE FROM relationships WHERE source_entity_id = 2 OR target_entity_id = 2")
    c.execute("DELETE FROM mentions WHERE entity_id = 2")
    c.execute("DELETE FROM entities WHERE id = 2")
    print("✓ Test entity (ID 2) deleted.")

    # 2. RENAME ID 29 to Раднаасумбэрэлийн Гончигдорж
    c.execute("""
        UPDATE entities 
        SET name = 'Раднаасумбэрэлийн Гончигдорж',
            description = 'Монгол Улсын дэд ерөнхийлөгч (1990-1992), УИХ-ын дарга (1996-2000), УИХ-ын дэд дарга (2012-2016).'
        WHERE id = 29
    """)
    # Add alias Р.Гончигдорж
    c.execute("""
        INSERT OR IGNORE INTO entity_aliases (entity_id, alias, alias_norm, kind)
        VALUES (29, 'Р.Гончигдорж', 'р гончигдорж', 'initials')
    """)
    print("✓ Entity 29 renamed to 'Раднаасумбэрэлийн Гончигдорж'.")

    # 3. MERGES LIST
    # (source_id, survivor_id, alias_to_add)
    merges = [
        (389, 388, "Д.Бямбасүрэнгийн танхим"),
        (386, 127, "С.Амарсайхан"),
        (172, 127, "Сайнбуяны Амарсайхан"),
        (391, 245, "Р.Амаржаргал"),
        (392, 255, "Су.Батболд"),
        (147, 230, "Жадамбаагийн Энхбаяр"),
        (248, 58, "Хавдсиламын Баделхан"),
        (23, 93, "С.Бямбацогт"),
        (28, 61, "Г.Занданшатар"),
        (19, 270, "Д.Дэмбэрэл"),
        (24, 234, "Л.Болд"),
        (377, 237, "Д.Ганболд"),
    ]

    for src_id, surv_id, extra_alias in merges:
        src_row = c.execute("SELECT id, name FROM entities WHERE id=?", (src_id,)).fetchone()
        surv_row = c.execute("SELECT id, name FROM entities WHERE id=?", (surv_id,)).fetchone()
        if not src_row or not surv_row:
            print(f"! Skipping merge {src_id} -> {surv_id}: entity not found.")
            continue

        src_name = src_row[1]
        surv_name = surv_row[1]

        # A. Move facts, avoiding exact duplicates
        src_facts = c.execute("SELECT id, fact_type, fact_date, fact_text FROM facts WHERE entity_id=?", (src_id,)).fetchall()
        for fid, ftype, fdate, ftext in src_facts:
            dup = c.execute("""
                SELECT id FROM facts 
                WHERE entity_id=? AND fact_type=? AND fact_text=?
            """, (surv_id, ftype, ftext)).fetchone()
            if dup:
                # Delete duplicate fact from source
                c.execute("DELETE FROM facts WHERE id=?", (fid,))
            else:
                # Reassign fact to survivor
                c.execute("UPDATE facts SET entity_id=? WHERE id=?", (surv_id, fid))

        # B. Move outgoing relationships, avoiding duplicates
        src_out_rels = c.execute("""
            SELECT id, rel_type, target_name, target_entity_id, start_date 
            FROM relationships WHERE source_entity_id=?
        """, (src_id,)).fetchall()
        for rid, rtype, tname, teid, sdate in src_out_rels:
            dup = c.execute("""
                SELECT id FROM relationships 
                WHERE source_entity_id=? AND target_name=? AND rel_type=?
            """, (surv_id, tname, rtype)).fetchone()
            if dup:
                c.execute("DELETE FROM relationships WHERE id=?", (rid,))
            else:
                c.execute("UPDATE relationships SET source_entity_id=? WHERE id=?", (surv_id, rid))

        # C. Move incoming relationships, avoiding duplicates
        src_in_rels = c.execute("""
            SELECT id, rel_type, source_entity_id 
            FROM relationships WHERE target_entity_id=?
        """, (src_id,)).fetchall()
        for rid, rtype, seid in src_in_rels:
            dup = c.execute("""
                SELECT id FROM relationships 
                WHERE target_entity_id=? AND source_entity_id=? AND rel_type=?
            """, (surv_id, seid, rtype)).fetchone()
            if dup:
                c.execute("DELETE FROM relationships WHERE id=?", (rid,))
            else:
                c.execute("UPDATE relationships SET target_entity_id=? WHERE id=?", (surv_id, rid))

        # D. Move mentions
        surv_mentions = {
            (m[0], m[1]) for m in c.execute("SELECT source_id, name_as_written FROM mentions WHERE entity_id=?", (surv_id,)).fetchall()
        }
        for mid, msid, mname in c.execute("SELECT id, source_id, name_as_written FROM mentions WHERE entity_id=?", (src_id,)).fetchall():
            if (msid, mname) in surv_mentions:
                c.execute("DELETE FROM mentions WHERE id=?", (mid,))
            else:
                c.execute("UPDATE mentions SET entity_id=? WHERE id=?", (surv_id, mid))

        # E. Move aliases
        surv_alias_norms = {
            a[0] for a in c.execute("SELECT alias_norm FROM entity_aliases WHERE entity_id=?", (surv_id,)).fetchall()
        }
        # Add src_name as alias if not exists
        src_clean = src_name.replace("'''", "").strip()
        src_norm = " ".join(src_clean.lower().replace(".", " ").split())
        if src_norm not in surv_alias_norms:
            c.execute("""
                INSERT OR IGNORE INTO entity_aliases (entity_id, alias, alias_norm, kind)
                VALUES (?, ?, ?, 'merged')
            """, (surv_id, src_clean, src_norm))
            surv_alias_norms.add(src_norm)

        if extra_alias:
            ex_norm = " ".join(extra_alias.lower().replace(".", " ").split())
            if ex_norm not in surv_alias_norms:
                c.execute("""
                    INSERT OR IGNORE INTO entity_aliases (entity_id, alias, alias_norm, kind)
                    VALUES (?, ?, ?, 'initials')
                """, (surv_id, extra_alias, ex_norm))

        # Move existing aliases of source
        for aid, aalias, anorm, akind in c.execute("SELECT id, alias, alias_norm, kind FROM entity_aliases WHERE entity_id=?", (src_id,)).fetchall():
            existing = c.execute("SELECT id FROM entity_aliases WHERE entity_id=? AND alias_norm=?", (surv_id, anorm)).fetchone()
            if not existing:
                c.execute("UPDATE entity_aliases SET entity_id=? WHERE id=?", (surv_id, aid))
                surv_alias_norms.add(anorm)
            else:
                c.execute("DELETE FROM entity_aliases WHERE id=?", (aid,))

        # F. Mark source as merged (tombstone)
        c.execute("UPDATE entities SET merged_into_id=? WHERE id=?", (surv_id, src_id))
        print(f"✓ Merged ID {src_id} ('{src_name}') -> ID {surv_id} ('{surv_name}')")

    # 4. FIX NULL FACT_IDS
    null_facts = c.execute("SELECT id FROM facts WHERE fact_id IS NULL OR fact_id = ''").fetchall()
    for (fid,) in null_facts:
        c.execute("UPDATE facts SET fact_id=? WHERE id=?", (f"F{fid}", fid))
    print(f"✓ Fixed {len(null_facts)} facts with null fact_id.")

    # 5. SYNTHESIZE BASELINE CHRONOLOGICAL FACTS FROM ESTABLISHED RELATIONSHIPS
    # Parliament dates map
    parl_dates = {
        "УИХ 1990–1992 (Шилжилтийн)": "1990-09-01",
        "УИХ 1990–1992": "1990-09-01",
        "УИХ 1992–1996": "1992-07-01",
        "УИХ 1996–2000": "1996-07-01",
        "УИХ 2000–2004": "2000-07-01",
        "УИХ 2004–2008": "2004-07-01",
        "УИХ 2008–2012": "2008-07-01",
        "УИХ 2012–2016": "2012-07-01",
        "УИХ 2016–2020": "2016-07-01",
        "УИХ 2020–2024": "2020-07-01",
        "УИХ 2024–2028": "2024-07-01",
    }

    # Government start dates map
    gov_dates = {
        "Д.Бямбасүрэнгийн танхим (1990–1992)": "1990-09-11",
        "Жасрайн Засгийн газар": "1992-07-21",
        "Энхсайханы Засгийн газар": "1996-11-01",
        "Элбэгдоржийн I Засгийн газар": "1998-04-01",
        "Энхбаярын Засгийн газар": "2000-07-26",
        "Элбэгдоржийн II Засгийн газар (Их эвсэл)": "2004-08-20",
        "Энхболдын Засгийн газар (Үндэсний эв нэгдэл)": "2006-01-25",
        "Баярын Засгийн газар": "2007-11-22",
        "Батболдын Засгийн газар": "2009-10-29",
        "Алтанхуягийн Шинэчлэлийн Засгийн газар": "2012-08-10",
        "Сайханбилэгийн Засгийн газар": "2014-11-21",
        "Ж.Эрдэнэбатын Засгийн газар (2016–2017)": "2016-07-08",
        "Хүрэлсүхийн Засгийн газар": "2017-10-04",
        "Оюун-Эрдэнийн Засгийн газар": "2021-01-27",
    }

    active_persons = c.execute("""
        SELECT id, name FROM entities 
        WHERE entity_type = 'person' AND merged_into_id IS NULL
    """).fetchall()

    new_facts_count = 0

    for pid, pname in active_persons:
        rels = c.execute("""
            SELECT r.id, r.rel_type, r.target_name, r.target_entity_id, e.name as target_entity_name, e.entity_type
            FROM relationships r
            LEFT JOIN entities e ON r.target_entity_id = e.id
            WHERE r.source_entity_id = ?
        """, (pid,)).fetchall()

        for rid, rtype, tname, teid, tename, tetype in rels:
            t_title = tename or tname
            fact_date = None
            fact_text = None
            role_ctx = None
            tags = []

            # A. Parliament MP relationship
            if "УИХ" in t_title or tetype == "parliament":
                for parl_key, pdate in parl_dates.items():
                    if parl_key in t_title:
                        fact_date = pdate
                        role_ctx = "УИХ-ын гишүүн"
                        fact_text = f"{pname} нь {parl_key}-ын гишүүнээр сонгогдон ажилласан."
                        tags = ["парламент", "уих-ын_гишүүн"]
                        break

            # B. Cabinet / Minister relationship
            elif "Засгийн газар" in t_title or "танхим" in t_title or tetype == "government":
                for gov_key, gdate in gov_dates.items():
                    if gov_key in t_title:
                        fact_date = gdate
                        # Extract minister title if in rtype, e.g. "сайд (Гадаад харилцааны сайд)"
                        if "сайд" in rtype:
                            import re
                            m = re.search(r'\((.*?)\)', rtype)
                            minister_role = m.group(1) if m else rtype
                            fact_text = f"{pname} нь {gov_key}-т {minister_role}-аар ажилласан."
                            role_ctx = minister_role
                        else:
                            fact_text = f"{pname} нь {gov_key}-т {rtype}-аар ажилласан."
                            role_ctx = rtype
                        tags = ["засгийн_газар", "сайд"]
                        break

            if fact_text and fact_date:
                # Check if exact fact already exists
                exists = c.execute("""
                    SELECT id FROM facts 
                    WHERE entity_id = ? AND fact_text = ?
                """, (pid, fact_text)).fetchone()

                if not exists:
                    c.execute("""
                        INSERT INTO facts (
                            entity_id, fact_type, fact_date, date_precision, 
                            fact_text, role_context, tags
                        ) VALUES (?, 'chronological', ?, 'year', ?, ?, ?)
                    """, (pid, fact_date, fact_text, role_ctx, json.dumps(tags, ensure_ascii=False)))
                    new_fid = c.lastrowid
                    c.execute("UPDATE facts SET fact_id = ? WHERE id = ?", (f"F{new_fid}", new_fid))
                    new_facts_count += 1

    print(f"✓ Synthesized {new_facts_count} baseline chronological facts from relationships.")

    # 6. UPDATE IS_STUB FLAGS
    # Entities with 0 facts and 0 rels are stubs; otherwise not
    c.execute("""
        UPDATE entities
        SET is_stub = CASE
            WHEN (SELECT count(*) FROM facts WHERE entity_id = entities.id) = 0
             AND (SELECT count(*) FROM relationships WHERE source_entity_id = entities.id) = 0
            THEN 1 ELSE 0 END
        WHERE merged_into_id IS NULL
    """)
    stubs_count = c.execute("SELECT count(*) FROM entities WHERE is_stub = 1 AND merged_into_id IS NULL").fetchone()[0]
    print(f"✓ Updated is_stub flags: {stubs_count} true stubs remaining.")

    conn.commit()
    conn.close()
    print("✓ All cleanup and standardization steps completed successfully!")

if __name__ == "__main__":
    run_cleanup()
