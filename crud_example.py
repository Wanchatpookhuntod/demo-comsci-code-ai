"""ตัวอย่าง CRUD บน Firestore — collection: users"""
from firestore_client import get_client

db = get_client()
COLLECTION = "users"


def create(user_id: str, data: dict) -> None:
    """สร้าง/เขียนทับเอกสาร"""
    db.collection(COLLECTION).document(user_id).set(data)
    print(f"[CREATE] {user_id} -> {data}")


def read(user_id: str) -> dict | None:
    """อ่านเอกสารตาม id"""
    doc = db.collection(COLLECTION).document(user_id).get()
    if doc.exists:
        print(f"[READ] {user_id} -> {doc.to_dict()}")
        return doc.to_dict()
    print(f"[READ] ไม่พบเอกสาร {user_id}")
    return None


def update(user_id: str, fields: dict) -> None:
    """อัปเดตบางฟิลด์ (merge)"""
    db.collection(COLLECTION).document(user_id).update(fields)
    print(f"[UPDATE] {user_id} <- {fields}")


def delete(user_id: str) -> None:
    """ลบเอกสาร"""
    db.collection(COLLECTION).document(user_id).delete()
    print(f"[DELETE] {user_id}")


def list_all() -> None:
    """ดึงทุกเอกสารใน collection"""
    print("[LIST]")
    for doc in db.collection(COLLECTION).stream():
        print(f"  - {doc.id}: {doc.to_dict()}")


if __name__ == "__main__":
    # ลองรันครบวงจร CRUD
    create("u001", {"name": "Wanchat", "age": 30, "active": True})
    read("u001")
    update("u001", {"age": 31})
    read("u001")
    list_all()
    delete("u001")
    read("u001")
