# Project: Student Attendance System with Geofencing
## Stack: Flask + Firestore + Leaflet.js

You are a senior full-stack engineer. Build a production-ready student check-in system with GPS verification. Backend uses Flask + Firestore. Frontend uses Leaflet.js for all map interactions (no Google Maps, no Mapbox, only Leaflet + OpenStreetMap tiles).

## 🎯 Objective
- Backend REST API for attendance logic
- Frontend web app with interactive maps for:
  - Student: see their location, classroom geofence, check-in button
  - Instructor: see live dots of students who checked in, draw/edit geofence
  - Admin: manage all classrooms on a campus map

## 🛠 Tech Stack

### Backend
- Flask 3.x, Flask-Smorest, Flask-JWT-Extended, Flask-CORS, Flask-Limiter
- Google Cloud Firestore (Native mode) + `google-cloud-firestore` SDK
- Pydantic v2, passlib (bcrypt), pygeohash, structlog
- Celery + Redis (background tasks)
- pytest + Firestore emulator

### Frontend
- **Leaflet.js 1.9+** (vanilla JS, no React/Vue required for MVP)
- **OpenStreetMap** tiles (default), with config to swap to Esri/Carto
- **Leaflet plugins** (use these exact ones):
  - `leaflet-draw` for instructor to draw circle geofence
  - `leaflet.markercluster` for many student dots
  - `leaflet-routing-machine` (optional, for "distance to classroom" UX)
  - `leaflet.locatecontrol` for "find me" button
- **HTML/CSS/JS**: vanilla + minimal Alpine.js or Stimulus for reactivity, NO heavy SPA framework
- **Build**: no bundler needed for MVP, serve static files from Flask
- **Realtime**: Server-Sent Events (SSE) from Flask, NOT WebSockets (simpler, fits HTTP)

## 📁 Project Structure
```
attendance_system/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── config.py
│   ├── firestore_client.py
│   ├── models/                  # Pydantic models
│   ├── repositories/            # Firestore data access
│   ├── api/                     # JSON REST endpoints (prefix /api/v1)
│   │   ├── auth.py
│   │   ├── students.py
│   │   ├── instructors.py
│   │   ├── admin.py
│   │   ├── attendance.py
│   │   ├── sessions.py
│   │   └── reports.py
│   ├── web/                     # Jinja2 HTML routes (server-rendered shell)
│   │   ├── __init__.py
│   │   ├── auth_views.py
│   │   ├── student_views.py
│   │   ├── instructor_views.py
│   │   └── admin_views.py
│   ├── sse/                     # Server-Sent Events streams
│   │   └── live_session.py
│   ├── services/
│   │   ├── geofence.py
│   │   ├── attendance_service.py
│   │   └── anti_cheat.py
│   ├── schemas/
│   ├── utils/
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html
│   │   ├── auth/login.html
│   │   ├── student/
│   │   │   ├── dashboard.html   # has Leaflet map
│   │   │   ├── checkin.html     # main check-in map view
│   │   │   └── history.html
│   │   ├── instructor/
│   │   │   ├── dashboard.html
│   │   │   ├── session_create.html  # draw geofence on map
│   │   │   └── session_live.html    # live dots map
│   │   └── admin/
│   │       ├── users.html
│   │       └── campus_map.html
│   └── static/
│       ├── css/
│       │   ├── app.css
│       │   └── leaflet-custom.css
│       ├── js/
│       │   ├── api.js               # fetch wrapper with JWT
│       │   ├── auth.js
│       │   ├── leaflet-base.js      # map factory, common config
│       │   ├── geo.js               # haversine, geolocation wrapper
│       │   ├── student-checkin.js   # main check-in UI logic
│       │   ├── instructor-create.js # draw circle geofence
│       │   ├── instructor-live.js   # SSE consumer + dot updates
│       │   └── admin-map.js
│       └── img/
│           ├── marker-student.svg
│           ├── marker-classroom.svg
│           └── marker-self.svg
├── firestore.indexes.json
├── firestore.rules
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🗄 Firestore Data Model (same as previous spec, key collections)

### `/sessions/{sessionId}`
```python
{
  "id": "uuid",
  "course_id": "uuid",
  "course_code": "CS101",
  "course_name": "Intro to CS",
  "instructor_id": "uuid",
  "instructor_name": "Dr. X",
  "start_at": Timestamp,
  "end_at": Timestamp,
  "center_lat": 13.7563,
  "center_lng": 100.5018,
  "geohash": "w4rqy",
  "radius_m": 100,
  "late_after_min": 15,
  "checkin_opens_min_before": 15,
  "checkin_closes_min_after": 30,
  "room": "ENG201",
  "building": "Engineering Building",
  "mode": "onsite" | "online" | "hybrid",
  "status": "scheduled" | "active" | "ended" | "cancelled",
  "created_at": Timestamp,
}
```

### `/attendance/{recordId}` (doc id = `{session_id}_{student_id}`)
```python
{
  "session_id": "uuid",
  "course_id": "uuid",
  "student_id": "uuid",
  "student_code": "65010001",
  "student_name": "...",
  "checkin_at": Timestamp,
  "checkin_lat": Number,
  "checkin_lng": Number,
  "checkin_accuracy_m": Number,
  "checkout_at": Timestamp | null,
  "checkout_lat": Number | null,
  "checkout_lng": Number | null,
  "status": "present" | "late" | "absent" | "leave" | "suspicious",
  "device_fingerprint": "string",
  "is_mock_location": false,
  "distance_from_center_m": Number,
  "flags": [],
  "created_at": Timestamp,
  "updated_at": Timestamp,
}
```

(Users, Courses, LeaveRequests, AuditLogs as in previous SQL/Firestore spec)

## 🔐 Backend API (prefix /api/v1)

### Auth
- POST /auth/login → JWT pair
- POST /auth/refresh
- POST /auth/logout
- GET /auth/me

### Student
- GET /me/sessions/today
- GET /me/sessions/active
- POST /me/checkin
- POST /me/checkout
- GET /me/attendance
- GET /me/stats

### Instructor
- POST /courses
- GET /courses/my
- POST /courses/{id}/sessions
- GET /sessions/{id}
- GET /sessions/{id}/roster
- PATCH /sessions/{id}              # update geofence center/radius
- PATCH /attendance/{id}/override
- GET /reports/course/{id}?format=json|csv|xlsx

### Admin
- CRUD /admin/users
- CRUD /admin/courses
- GET /admin/sessions                # for campus-wide map (with geofence circles)
- GET /admin/audit-logs
- PATCH /admin/policy

### SSE (realtime)
- GET /sse/sessions/{id}/live        # emits events: 'checkin', 'checkout', 'override'
- GET /sse/sessions/{id}/heartbeat   # keep-alive every 15s

## 🌐 Web Routes (Jinja2 server-rendered, all use Leaflet)

### Public
- GET /login → login form
- GET /logout

### Student (`/me/*`)
- GET /me                            # dashboard with map of today's sessions
- GET /me/checkin/{session_id}       # MAIN check-in view (large map)
- GET /me/history                    # past attendance with mini maps

### Instructor (`/i/*`)
- GET /i                             # dashboard
- GET /i/courses/{id}                # course detail
- GET /i/sessions/new                # create session: pick location on map, draw radius
- GET /i/sessions/{id}/live          # live map of students (uses SSE)
- GET /i/sessions/{id}/report        # post-session map showing all check-in pins

### Admin (`/admin/*`)
- GET /admin                         # users + audit
- GET /admin/campus-map              # all classrooms + geofences on one map

## 🗺 Leaflet UI Specifications (CRITICAL - implement exactly)

### Common map factory (`static/js/leaflet-base.js`)
```javascript
// Exports createMap(elementId, options)
// Default center: campus center from config endpoint /api/v1/config/campus
// Default zoom: 17
// Tile layer: OpenStreetMap with attribution
// Provide light/dark theme switch via CSS class
// Add scale control bottom-left
// Add zoom control top-right
```

### Student Check-in View (`templates/student/checkin.html` + `static/js/student-checkin.js`)

Layout (mobile-first, max-width 480px):
- Top: course name, room, time window countdown
- Middle: Leaflet map (height 60vh)
- Bottom: large "Check In" button (sticky)
- Status bar: "Distance from classroom: 42m" updates live

Map MUST show:
1. **Classroom marker** (custom icon, marker-classroom.svg) at session.center_lat/lng
2. **Geofence circle** using `L.circle()` with radius_m, semi-transparent fill (#22c55e at 20% opacity, border solid)
3. **Student location marker** (marker-self.svg) updates every 5s using `navigator.geolocation.watchPosition`
4. **Accuracy circle** around student (`L.circle` with radius = position.accuracy, dashed border)
5. **Line/polyline** from student to classroom center, color changes:
   - Green if inside geofence
   - Orange if within 1.5x radius
   - Red if far away

Interactions:
- Auto-pan to fit both markers using `map.fitBounds()`
- "Find Me" button (leaflet.locatecontrol) recenter on user
- Tap classroom marker → popup with room number + walking distance estimate
- Check-in button disabled until: GPS accuracy < 30m AND inside geofence AND not already checked in
- Button shows reason if disabled (e.g., "Move closer, you're 120m away")
- On check-in success: marker turns gold, button shows "Checked in at 09:02 ✓", confetti animation (optional)
- On check-in failure: toast with specific error from API

Anti-cheat detection on client (also enforced server-side):
- Check `navigator.permissions.query({name:'geolocation'})` state
- For Android via Cordova/Capacitor wrapper, check mock location flag (document as TODO if pure web)
- Fingerprint device via `crypto.subtle` over: userAgent + screen + timezone + canvas hash, send as `device_fingerprint`

### Instructor Session Create (`templates/instructor/session_create.html` + `static/js/instructor-create.js`)

Layout:
- Left panel: form (course select, date/time, room, late threshold)
- Right panel: Leaflet map (height 70vh)

Map behavior:
1. Initial center: campus center
2. Search box top-left: use Nominatim API (OSM) for address search, free, no API key
```javascript
   // Use leaflet-control-geocoder plugin with Nominatim provider
```
3. Click on map → drop classroom marker at clicked point
4. After marker placed → automatically add `L.circle` with default radius 100m
5. Radius slider in form (10m to 500m) updates circle live
6. Drag marker to fine-tune center
7. Show coordinates display: "Center: 13.7563°N, 100.5018°E"
8. Form submit → POST /api/v1/courses/{id}/sessions with center_lat, center_lng, radius_m

Validation:
- Cannot submit without map pin placed
- Warn if radius > 500m (likely too large)
- Show preview: "This circle covers approximately X m²"

### Instructor Live View (`templates/instructor/session_live.html` + `static/js/instructor-live.js`)

Layout:
- Top: session info + stats (Present: 23, Late: 4, Absent: 8)
- Map: full width, height 60vh
- Bottom: scrollable roster list, click name → highlight pin on map

Map shows:
1. Classroom marker + geofence circle
2. **Marker cluster** of all checked-in students (use `Leaflet.markercluster`)
3. Each student marker:
   - Green if status=present, orange if late, red if suspicious
   - Popup: student_code + name + check-in time + distance
4. **SSE subscription** to `/sse/sessions/{id}/live`:
   - On 'checkin' event: add new marker with pulse animation (CSS @keyframes)
   - On 'checkout' event: dim marker
   - On 'override' event: update marker color
5. Auto-refresh stats counter without page reload
6. "Export PNG" button: use `leaflet-image` plugin to snapshot map for report
7. "Toggle heatmap" using `leaflet.heat` plugin showing density (optional, nice-to-have)

SSE client pattern:
```javascript
const evt = new EventSource(`/sse/sessions/${sessionId}/live?token=${jwt}`);
evt.addEventListener('checkin', (e) => {
  const data = JSON.parse(e.data);
  addStudentMarker(data);
});
evt.addEventListener('heartbeat', () => { /* update last-sync indicator */ });
```

### Admin Campus Map (`templates/admin/campus_map.html` + `static/js/admin-map.js`)

Map shows ALL active + upcoming sessions across campus:
1. Each session = classroom marker + geofence circle
2. Marker color = session.status (scheduled=blue, active=green, ended=gray)
3. Click marker → popup with course, instructor, attendance count, link to live view
4. Filter panel: by building, by instructor, by time range
5. Layer toggle: heatmap of attendance density (use `leaflet.heat`)
6. List view sidebar synced with map (click row → zoom to marker)

## 🧭 Geolocation Client Logic (`static/js/geo.js`)

```javascript
// Wrap navigator.geolocation with promise + watch API
export function watchLocation(callback, options = {}) {
  const opts = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 0,
    ...options,
  };
  return navigator.geolocation.watchPosition(
    pos => callback({
      lat: pos.coords.latitude,
      lng: pos.coords.longitude,
      accuracy: pos.coords.accuracy,
      timestamp: pos.timestamp,
    }),
    err => callback(null, err),
    opts,
  );
}

export function haversineMeters(lat1, lng1, lat2, lng2) {
  // standard formula, return meters
}

export function isInsideGeofence(point, center, radiusM) {
  return haversineMeters(point.lat, point.lng, center.lat, center.lng) <= radiusM;
}
```

## 🛡 Security
- JWT stored in httpOnly cookie (not localStorage) for web routes
- For SSE: pass token via query param (EventSource cannot set headers) but rotate token regularly
- CSRF token on form POSTs from Jinja templates
- Content Security Policy: allow self + OpenStreetMap tile servers + Nominatim
- Rate limit Nominatim proxy via Flask (don't hit OSM directly from many clients, proxy via /api/v1/geocode)
- Sanitize all popup content (XSS via student names)
- Server-side validation of EVERY check-in even if client claims valid

## 🧪 Testing
- Backend: pytest + Firestore emulator, ≥ 80% coverage
- Frontend: Playwright E2E for critical flows:
  - Student opens check-in page, geofence circle renders, mock geolocation, button enables, submit succeeds
  - Instructor creates session: click map, drag, set radius, save, verify Firestore doc
  - Instructor live view: SSE event fires, new marker appears
- Mock geolocation in Playwright: `context.setGeolocation({latitude, longitude})`

## 📦 Deliverables (in order)
1. `requirements.txt`, `package.json` (optional for Playwright), `.env.example`
2. `docker-compose.yml` (firestore-emulator, redis, web, celery)
3. Flask scaffolding + Firestore client
4. All Pydantic models + repositories
5. All API endpoints with OpenAPI docs
6. SSE endpoint with token auth
7. Jinja2 base template + auth views
8. Leaflet base JS (createMap factory) + custom CSS
9. Student check-in view (HTML + JS)
10. Instructor session create view
11. Instructor live view + SSE consumer
12. Admin campus map
13. `flask seed-demo` CLI: creates demo data with Bangkok coordinates (e.g., Chulalongkorn or Mahidol campus)
14. Tests (pytest + Playwright)
15. README with screenshots, setup steps, deploy notes

## 📐 Code Style
- Python 3.11+, full type hints
- JS: ES modules, no jQuery, modern fetch API
- CSS: vanilla or Tailwind via CDN (no build step)
- Mobile-first responsive (test at 375px width)
- All maps must work without JS errors in browser console
- Lighthouse score ≥ 85 on student check-in page

## ⚠️ Constraints
- DO NOT use Google Maps, Mapbox, or any paid map provider
- DO NOT use React, Vue, Svelte, Next.js - vanilla JS + Alpine.js max
- DO NOT load Leaflet from random CDNs - use unpkg.com or self-host
- DO NOT trust client geolocation - always re-verify on server
- DO NOT expose Firestore directly to client - all access via Flask API
- DO NOT use `L.marker` without custom icon (default icon paths break in Flask static serving - configure `L.Icon.Default.imagePath` correctly)
- DO NOT forget HTTPS requirement for `navigator.geolocation` in production
- Tile usage MUST respect OSM tile usage policy (add User-Agent header on server-side proxy if used)

## ✅ Acceptance Criteria
- [ ] `docker-compose up` starts everything cleanly
- [ ] Student can: login → see today's sessions → open check-in map → see classroom + own location → check in successfully when inside radius
- [ ] Map shows distance updating live as user moves (simulated via browser devtools geolocation override)
- [ ] Check-in button correctly disables when outside radius / low accuracy / mock detected
- [ ] Instructor can: create course → create session by clicking on map → save with custom radius
- [ ] Instructor live view: open in 2 tabs, when student checks in via API, new marker appears in both tabs within 2s
- [ ] Admin campus map shows all sessions with correct geofence circles
- [ ] All maps load without console errors
- [ ] OpenAPI docs at /api/v1/docs
- [ ] Tests pass: pytest + at least 3 Playwright scenarios

Begin with backend scaffolding (deliverables 1-7), then move to Leaflet base + student view (deliverable 8-9), which is the highest-value path. Pause for review after deliverable 9 before continuing.