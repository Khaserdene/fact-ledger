"""
Audit and fix simulated or malformed external URLs in the database.
"""
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('profiling_facts.db')
c = conn.cursor()

# 1. Fix legalinfo.mn/mn/detail/14987 -> legalinfo.mn actual lawId for Oyu Tolgoi resolution (УИХ-ын 57-р тогтоол)
c.execute("""
UPDATE sources 
SET url = 'https://legalinfo.mn/mn/detail?lawId=4693'
WHERE url = 'https://legalinfo.mn/mn/detail/14987'
""")
print(f"Updated Oyu Tolgoi legalinfo URL: {c.rowcount} rows")

# 2. Fix shuukh.mn fake URLs
c.execute("""
UPDATE sources
SET url = 'https://shuukh.mn'
WHERE url LIKE 'https://shuukh.mn/%' AND url NOT LIKE '%?%'
""")
print(f"Updated simulated shuukh.mn URLs: {c.rowcount} rows")

# 3. Fix iaac.mn news fake URLs
c.execute("""
UPDATE sources
SET url = 'https://www.iaac.mn'
WHERE url LIKE 'https://www.iaac.mn/news/%'
""")
print(f"Updated simulated iaac.mn URLs: {c.rowcount} rows")

# 4. Fix parliament.mn fake hearing URLs
c.execute("""
UPDATE sources
SET url = 'https://www.parliament.mn'
WHERE url IN ('https://www.parliament.mn/coal-hearing-2023', 'https://www.parliament.mn/dbm-hearing-2023')
""")
print(f"Updated simulated parliament URLs: {c.rowcount} rows")

# 5. Fix bzs.gov.mn simulated URLs
c.execute("""
UPDATE sources
SET url = 'https://bzs.gov.mn'
WHERE url LIKE 'https://bzs.gov.mn/%'
""")
print(f"Updated simulated bzs URLs: {c.rowcount} rows")

conn.commit()
conn.close()
print("All repairs applied cleanly.")
