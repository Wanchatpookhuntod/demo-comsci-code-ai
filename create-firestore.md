# ขั้นตอนการตั้งค่า Firestore

คู่มือสร้างและตั้งค่า Firestore สำหรับโปรเจกต์นี้ (Python + service account)

---

## 1. สร้าง Project บน Google Cloud / Firebase

1. เข้า [Firebase Console](https://console.firebase.google.com/) แล้วกด **Add project** (หรือใช้ project เดิมจาก [Google Cloud Console](https://console.cloud.google.com/))
2. ตั้งชื่อ project แล้วทำตามขั้นตอนจนเสร็จ
3. จด **Project ID** ไว้ (จะใช้ตอนเชื่อมต่อ)

---

## 2. เปิดใช้งาน Firestore Database

1. ใน Firebase Console เลือกเมนู **Build → Firestore Database**
2. กด **Create database**
3. เลือกโหมด:
   - **Production mode** — ปลอดภัย ต้องตั้ง Security Rules เอง (แนะนำ)
   - **Test mode** — เปิดอ่าน/เขียนได้หมดชั่วคราว (ใช้ทดลองเท่านั้น)
4. เลือก **Location** (เช่น `asia-southeast1` = สิงคโปร์ ใกล้ไทยสุด) — **เลือกแล้วเปลี่ยนไม่ได้**
5. กด **Enable**

> โปรเจกต์นี้ใช้ database id แบบกำหนดเอง คือ **`demo-cs-1`** (ไม่ใช่ `(default)`)
> ถ้าจะสร้าง database เพิ่มที่ไม่ใช่ default ให้ไปที่ Google Cloud Console → Firestore → Create database แล้วตั้ง Database ID เอง

---

## 3. สร้าง Service Account Key

1. ไปที่ [Google Cloud Console → IAM & Admin → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. เลือก project ให้ตรง แล้วกด **Create Service Account** (หรือใช้ตัวที่มีอยู่)
3. ตั้งชื่อ แล้วให้ role **Cloud Datastore User** หรือ **Firebase Admin** (สำหรับอ่าน/เขียน Firestore)
4. หลังสร้างเสร็จ เข้าไปที่ service account นั้น → แท็บ **Keys → Add Key → Create new key → JSON**
5. ดาวน์โหลดไฟล์ JSON มาวางในโฟลเดอร์โปรเจกต์ แล้วเปลี่ยนชื่อเป็น **`demo-cs.json`**

> ⚠️ **ห้าม commit ไฟล์ key ขึ้น git เด็ดขาด** — `.gitignore` ตั้ง ignore `*.json` ไว้แล้ว

---

## 4. ติดตั้ง Dependencies

```bash
# สร้าง virtual environment (ครั้งแรกเท่านั้น)
python3 -m venv .venv
source .venv/bin/activate

# ติดตั้ง library
pip install -r requirements.txt
```

`requirements.txt` ใช้:

```
google-cloud-firestore>=2.16.0
```

---

## 5. ตั้งค่าการเชื่อมต่อ

ค่าเชื่อมต่ออยู่ใน [firestore_client.py](firestore_client.py) — ถ้าเปลี่ยน project/database ให้แก้ที่นี่:

```python
SERVICE_ACCOUNT = os.path.join(BASE_DIR, "demo-cs.json")  # ชื่อไฟล์ key
DATABASE_ID = "demo-cs-1"                                   # database id
```

ทุกสคริปต์เรียก `get_client()` เพื่อรับ client ที่ auth แล้ว:

```python
from firestore_client import get_client
db = get_client()
```

---

## 6. ทดสอบการเชื่อมต่อ

```bash
python firestore_client.py
```

ถ้าสำเร็จจะขึ้น:

```
เชื่อมต่อ Firestore สำเร็จ — project: <project-id>, database: demo-cs-1
```

---

## 7. ใส่ข้อมูลตัวอย่าง / ลอง CRUD

```bash
# เขียนข้อมูลตัวอย่างลง collection "users"
python seed_data.py

# ลองครบวงจร create / read / update / delete
python crud_example.py
```

เปิด Firestore Database ใน Console แล้ว refresh จะเห็น collection **`users`**

---

## โครงสร้างไฟล์ในโปรเจกต์

| ไฟล์ | หน้าที่ |
|------|--------|
| [firestore_client.py](firestore_client.py) | สร้าง Firestore client จาก service account |
| [seed_data.py](seed_data.py) | เขียนข้อมูลตัวอย่างลง collection `users` |
| [crud_example.py](crud_example.py) | ตัวอย่าง CRUD ครบวงจร |
| `demo-cs.json` | service account key (ห้าม commit) |
| [requirements.txt](requirements.txt) | dependency ของโปรเจกต์ |

---

## หมายเหตุเรื่อง Security Rules

ถ้าเลือก **Production mode** ต้องตั้ง rules ใน Console → Firestore → Rules
ตัวอย่าง (เปิดให้เฉพาะผู้ที่ login):

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

> service account จะข้าม Security Rules อยู่แล้ว (สิทธิ์ระดับ admin) — rules มีผลกับ client SDK ฝั่ง user เท่านั้น
