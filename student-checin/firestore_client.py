"""สร้าง Firestore client จาก service account JSON ในโฟลเดอร์นี้"""
import os
from google.cloud import firestore

# path ของไฟล์ service account (อยู่โฟลเดอร์เดียวกับสคริปต์)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT = os.path.join(BASE_DIR, "demo-cs.json")

# database id ของ project นี้ (ไม่ใช่ "(default)")
DATABASE_ID = "demo-cs-1"


def get_client() -> firestore.Client:
    """คืน Firestore client ที่ auth ด้วย service account แล้ว"""
    return firestore.Client.from_service_account_json(
        SERVICE_ACCOUNT, database=DATABASE_ID
    )


if __name__ == "__main__":
    db = get_client()
    print(f"เชื่อมต่อ Firestore สำเร็จ — project: {db.project}, database: {db._database}")
