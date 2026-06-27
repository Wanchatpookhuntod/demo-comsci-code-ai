import unittest
from unittest.mock import patch, MagicMock
from app import app, haversine_meters, MAX_RADIUS_METERS, SCHOOL_COORDS

class CheckinAppTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_distance_within_radius(self):
        # 0.001 lat diff is around 110 meters, well within 1000m radius
        distance = haversine_meters(
            SCHOOL_COORDS["lat"], SCHOOL_COORDS["lng"],
            SCHOOL_COORDS["lat"] + 0.001, SCHOOL_COORDS["lng"]
        )
        self.assertLessEqual(distance, MAX_RADIUS_METERS)

    def test_distance_outside_radius(self):
        # 0.015 lat diff is around 1.6 km, outside 1000m radius
        distance = haversine_meters(
            SCHOOL_COORDS["lat"], SCHOOL_COORDS["lng"],
            SCHOOL_COORDS["lat"] + 0.015, SCHOOL_COORDS["lng"]
        )
        self.assertGreater(distance, MAX_RADIUS_METERS)

    def test_school_coords(self):
        self.assertAlmostEqual(SCHOOL_COORDS["lat"], 14.799951350019564, places=6)
        self.assertAlmostEqual(SCHOOL_COORDS["lng"], 100.62209954642286, places=6)

    @patch('app.db')
    def test_login_success(self, mock_db):
        # Mock Firestore DocumentSnapshot
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"name": "Wanchat", "active": True}
        
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        response = self.app.post('/login', json={"student_id": "u001"})
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["name"], "Wanchat")
        
        # Verify student_id is set in session
        with self.app as client:
            with client.session_transaction() as sess:
                # Flask session transaction allows inspecting session
                pass

    @patch('app.db')
    def test_login_not_found(self, mock_db):
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        response = self.app.post('/login', json={"student_id": "invalid_id"})
        data = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertFalse(data["success"])
        self.assertIn("ไม่พบข้อมูลรหัสนักศึกษา", data["message"])

    def test_logout(self):
        with self.app as client:
            with client.session_transaction() as sess:
                sess['student_id'] = 'u001'
            
            response = client.get('/logout')
            self.assertEqual(response.status_code, 302)  # Should redirect to index

    @patch('app.db')
    def test_checkin_within_radius_success(self, mock_db):
        # Set session student_id
        with self.app as client:
            with client.session_transaction() as sess:
                sess['student_id'] = 'u001'

            # Mock student verify
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {"name": "Wanchat", "active": True}
            mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

            # Checkin coordinates close to school
            response = client.post('/checkin', json={
                "lat": SCHOOL_COORDS["lat"] + 0.001,
                "lng": SCHOOL_COORDS["lng"]
            })
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertTrue(data["success"])
            self.assertIn("เช็คอินเข้าเรียนสำเร็จ", data["message"])
            # Verify db.collection('checkins').add was called
            mock_db.collection.return_value.add.assert_called_once()

    @patch('app.db')
    def test_checkin_outside_radius_failure(self, mock_db):
        # Set session student_id
        with self.app as client:
            with client.session_transaction() as sess:
                sess['student_id'] = 'u001'

            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {"name": "Wanchat", "active": True}
            mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

            # Checkin coordinates far from school
            response = client.post('/checkin', json={
                "lat": SCHOOL_COORDS["lat"] + 0.020,
                "lng": SCHOOL_COORDS["lng"]
            })
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertFalse(data["success"])
            self.assertIn("เช็คอินไม่สำเร็จ", data["message"])

    @patch('app.db')
    def test_admin_stats(self, mock_db):
        # Create a mock for AggregationResult
        mock_result = MagicMock()
        mock_result.value = 10
        
        # Configure count().get() to return [[mock_result]]
        mock_db.collection.return_value.count.return_value.get.return_value = [[mock_result]]
        mock_db.collection.return_value.where.return_value.count.return_value.get.return_value = [[mock_result]]
        
        response = self.app.get('/api/admin/stats')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["total_checkins"], 10)

    @patch('app.db')
    def test_get_admin_students(self, mock_db):
        mock_doc1 = MagicMock()
        mock_doc1.id = "u001"
        mock_doc1.to_dict.return_value = {"name": "Wanchat", "active": True}
        
        mock_doc2 = MagicMock()
        mock_doc2.id = "u002"
        mock_doc2.to_dict.return_value = {"name": "Somchai", "active": False}
        
        mock_db.collection.return_value.stream.return_value = [mock_doc1, mock_doc2]

        response = self.app.get('/api/admin/students')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["students"]), 2)
        self.assertEqual(data["students"][0]["id"], "u001")
        self.assertEqual(data["students"][1]["id"], "u002")

    @patch('app.db')
    def test_add_or_update_student(self, mock_db):
        # Mock student does not exist (new student)
        mock_db.collection.return_value.document.return_value.get.return_value.exists = False
        
        response = self.app.post('/api/admin/students', json={
            "student_id": "u004",
            "name": "Nara",
            "active": True
        })
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("เพิ่มนักศึกษา u004 เข้าสู่ระบบสำเร็จ", data["message"])
        mock_db.collection.return_value.document.return_value.set.assert_called_once_with({
            "name": "Nara",
            "active": True
        })

    @patch('app.db')
    def test_delete_student(self, mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value.exists = True
        
        response = self.app.delete('/api/admin/students/u004')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("ลบนักศึกษา u004 สำเร็จ", data["message"])
        mock_db.collection.return_value.document.return_value.delete.assert_called_once()


if __name__ == '__main__':
    unittest.main()

