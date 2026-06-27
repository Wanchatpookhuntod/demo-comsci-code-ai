import argparse
import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from firestore_client import get_client
from google.cloud import firestore

app = Flask(__name__)
app.secret_key = 'demo-cs-student-checkin-key'

SCHOOL_COORDS = {
    "lat": 14.799951350019564,
    "lng": 100.62209954642286,
}

MAX_RADIUS_METERS = 1000

# เชื่อมต่อ Firestore
db = get_client()


def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


@app.route('/')
def index():
    student = None
    student_id = session.get('student_id')
    if student_id:
        user_ref = db.collection('users').document(student_id).get()
        if user_ref.exists and user_ref.to_dict().get('active', True):
            user_data = user_ref.to_dict()
            student = {
                "id": student_id,
                "name": user_data.get('name', 'ไม่ระบุชื่อ')
            }
        else:
            session.clear()
            
    return render_template('index.html', 
                           SCHOOL_COORDS=SCHOOL_COORDS, 
                           MAX_RADIUS_METERS=MAX_RADIUS_METERS,
                           student=student)


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True)
        student_id = data.get('student_id', '').strip()
        password = data.get('password', '').strip()
        
        if not student_id:
            return jsonify({"success": False, "message": "กรุณากรอกรหัสนักศึกษา"}), 400
        if not password:
            return jsonify({"success": False, "message": "กรุณากรอกรหัสผ่าน"}), 400

        user_ref = db.collection('users').document(student_id).get()
        if user_ref.exists:
            user_data = user_ref.to_dict()
            if not user_data.get('active', True):
                return jsonify({"success": False, "message": "รหัสนักศึกษานี้ถูกระงับสิทธิ์ชั่วคราว"}), 403
                
            db_password = user_data.get('password', '123456')
            if password != db_password:
                return jsonify({"success": False, "message": "รหัสผ่านไม่ถูกต้อง"}), 401
                
            session['student_id'] = student_id
            session['student_name'] = user_data.get('name')
            return jsonify({
                "success": True, 
                "name": user_data.get('name')
            })
        else:
            return jsonify({"success": False, "message": "ไม่พบข้อมูลรหัสนักศึกษาในระบบ หรือรหัสไม่ถูกต้อง"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/checkin', methods=['POST'])
def checkin():
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบก่อนเช็คอิน"}), 401

        data = request.get_json(force=True)
        lat_val = data.get('lat')
        lng_val = data.get('lng')

        if lat_val is None or lng_val is None:
            return jsonify({"success": False, "message": "ไม่สามารถอ่านพิกัดพิกัดตำแหน่งได้"}), 400

        lat = float(lat_val)
        lng = float(lng_val)

        user_ref = db.collection('users').document(student_id).get()
        if not user_ref.exists:
            return jsonify({"success": False, "message": "รหัสนักศึกษาไม่มีสิทธิ์เช็คอิน"}), 403

        user_data = user_ref.to_dict()
        if not user_data.get('active', True):
            return jsonify({"success": False, "message": "รหัสนักศึกษานี้ถูกระงับสิทธิ์ชั่วคราว"}), 403

        name = user_data.get('name', 'ไม่ระบุชื่อ')
        distance = haversine_meters(lat, lng, SCHOOL_COORDS['lat'], SCHOOL_COORDS['lng'])

        if distance <= MAX_RADIUS_METERS:
            checkin_data = {
                "student_id": student_id,
                "name": name,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "lat": lat,
                "lng": lng,
                "distance_meters": round(distance),
                "status": "success"
            }
            db.collection('checkins').add(checkin_data)

            return jsonify({
                "success": True,
                "distance_meters": round(distance),
                "name": name,
                "message": "เช็คอินเข้าเรียนสำเร็จ ยินดีต้อนรับ!"
            })
        else:
            return jsonify({
                "success": False,
                "distance_meters": round(distance),
                "message": f"เช็คอินไม่สำเร็จ: คุณอยู่ห่างเกินกำหนด ({round(distance)} เมตร)"
            })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/history', methods=['GET'])
def get_history():
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบก่อน"}), 401

        checkins_ref = db.collection('checkins')
        docs = checkins_ref.where('student_id', '==', student_id).stream()
        
        history = []
        for doc in docs:
            d = doc.to_dict()
            history.append(d)
            
        # จัดเรียงตามเวลาในฝั่งเซิร์ฟเวอร์เพื่อไม่ให้ต้องทำ Composite Index
        history.sort(key=lambda x: x.get('timestamp') or datetime.min, reverse=True)
        history = history[:10]
        
        for d in history:
            ts = d.get('timestamp')
            if isinstance(ts, datetime):
                d['timestamp'] = ts.astimezone().strftime('%d/%m/%Y %H:%M:%S')
            elif ts is not None:
                d['timestamp'] = str(ts)
            else:
                d['timestamp'] = 'N/A'
                
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    try:
        checkins_ref = db.collection('checkins')
        students_ref = db.collection('users')
        
        try:
            checkins_count = checkins_ref.count().get()[0][0].value
        except Exception:
            checkins_count = len(list(checkins_ref.stream()))
            
        try:
            students_count = students_ref.count().get()[0][0].value
        except Exception:
            students_count = len(list(students_ref.stream()))
            
        try:
            active_students_count = students_ref.where('active', '==', True).count().get()[0][0].value
        except Exception:
            active_students_count = len([s for s in students_ref.stream() if s.to_dict().get('active', True)])
            
        return jsonify({
            "success": True,
            "total_checkins": checkins_count,
            "total_students": students_count,
            "active_students": active_students_count
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/admin/students', methods=['GET'])
def get_admin_students():
    try:
        students_ref = db.collection('users')
        docs = students_ref.stream()
        students = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            if 'active' not in d:
                d['active'] = True
            students.append(d)
        students.sort(key=lambda x: x['id'])
        return jsonify({"success": True, "students": students})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/admin/students', methods=['POST'])
def add_or_update_student():
    try:
        data = request.get_json(force=True)
        student_id = data.get('student_id', '').strip()
        name = data.get('name', '').strip()
        password = data.get('password', '').strip()
        active = data.get('active')
        
        if not student_id:
            return jsonify({"success": False, "message": "กรุณากรอกรหัสนักศึกษา"}), 400
            
        student_ref = db.collection('users').document(student_id)
        student_doc = student_ref.get()
        
        if student_doc.exists:
            fields = {}
            if name:
                fields['name'] = name
            if password:
                fields['password'] = password
            if active is not None:
                fields['active'] = active
            student_ref.update(fields)
            msg = f"อัปเดตข้อมูลนักศึกษา {student_id} สำเร็จ"
        else:
            if not name:
                return jsonify({"success": False, "message": "กรุณากรอกชื่อ-นามสกุล สำหรับนักศึกษาใหม่"}), 400
            if not password:
                return jsonify({"success": False, "message": "กรุณากรอกรหัสผ่าน สำหรับนักศึกษาใหม่"}), 400
            student_ref.set({
                "name": name,
                "password": password,
                "active": True if active is None else active
            })
            msg = f"เพิ่มนักศึกษา {student_id} เข้าสู่ระบบสำเร็จ"
            
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/admin/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        student_ref = db.collection('users').document(student_id)
        if not student_ref.get().exists:
            return jsonify({"success": False, "message": "ไม่พบข้อมูลนักศึกษานี้"}), 404
            
        student_ref.delete()
        return jsonify({"success": True, "message": f"ลบนักศึกษา {student_id} สำเร็จ"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/admin/checkins', methods=['GET'])
def get_all_checkins():
    try:
        checkins_ref = db.collection('checkins')
        query = checkins_ref.order_by('timestamp', direction=firestore.Query.DESCENDING)
        docs = query.stream()
        checkins = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            ts = d.get('timestamp')
            if isinstance(ts, datetime):
                d['timestamp'] = ts.astimezone().strftime('%d/%m/%Y %H:%M:%S')
            elif ts is not None:
                d['timestamp'] = str(ts)
            else:
                d['timestamp'] = 'N/A'
            checkins.append(d)
        return jsonify({"success": True, "checkins": checkins})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/admin/checkins/<checkin_id>', methods=['DELETE'])
def delete_checkin(checkin_id):
    try:
        checkin_ref = db.collection('checkins').document(checkin_id)
        if not checkin_ref.get().exists:
            return jsonify({"success": False, "message": "ไม่พบประวัติเช็คอินนี้"}), 404
            
        checkin_ref.delete()
        return jsonify({"success": True, "message": "ลบรายการเช็คอินสำเร็จ"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/admin/checkins', methods=['DELETE'])
def clear_all_checkins():
    try:
        checkins_ref = db.collection('checkins')
        batch = db.batch()
        docs = checkins_ref.stream()
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count >= 400:
                batch.commit()
                batch = db.batch()
                count = 0
        if count > 0:
            batch.commit()
        return jsonify({"success": True, "message": "ล้างประวัติการเช็คอินทั้งหมดเรียบร้อยแล้ว"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    app.run(debug=True, host=args.host, port=args.port)
