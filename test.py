from src.database.simple_db import SimpleDB

db = SimpleDB()

# Get all projects
projects = db.list_projects()

print("Current projects:")
for p in projects:
    print(f"  - {p['id']}: {p['title']}")

# Remove duplicates based on title
seen_titles = set()
duplicates = []

for p in projects:
    if p['title'] in seen_titles:
        duplicates.append(p['id'])
        print(f"\nDuplicate found: {p['title']} (ID: {p['id']})")
    else:
        seen_titles.add(p['title'])

# Delete duplicates
if duplicates:
    print(f"\nDeleting {len(duplicates)} duplicate(s)...")
    cursor = db.conn.cursor()
    for dup_id in duplicates:
        cursor.execute("DELETE FROM projects WHERE id = ?", (dup_id,))
    db.conn.commit()
    print("✅ Duplicates removed!")
else:
    print("\n✅ No duplicates found")

print("\nFinal projects:")
for p in db.list_projects():
    print(f"  - {p['title']}")