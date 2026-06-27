"""เขียนข้อมูลตัวอย่างลง Firestore แบบไม่ลบ — ไว้ดูใน console"""
from firestore_client import get_client

db = get_client()

users = [
    {"id": "u001", "name": "Wanchat", "age": 31, "active": True},
    {"id": "u002", "name": "Somchai", "age": 25, "active": True},
    {"id": "u003", "name": "Malee", "age": 28, "active": False},
]

for u in users:
    uid = u.pop("id")
    db.collection("users").document(uid).set(u)
    print(f"[SEED] users/{uid} -> {u}")

print("\nเขียนเสร็จแล้ว — เปิด console แล้วกด refresh จะเห็น collection 'users'")
