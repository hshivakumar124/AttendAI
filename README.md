# 🎓 AttendAI — Smart Classroom Intelligence & Attendance Platform

> Full-Stack Computer Vision Classroom Intelligence & Attendance Platform

AttendAI is an educational engineering reference platform designed for smart educational institutions. It demonstrates the end-to-end integration of 512-dimensional facial recognition, multi-object tracking, 3D head pose estimation, temporal drowsiness detection, electronic device distraction analysis, explainable visual engagement scoring, and real-time WebSocket telemetry into a unified dark-mode dashboard.

---

## 🌟 Key Platform Features

- **🔐 Biometric Consent & Opt-In Architecture**: Explicit opt-in consent is strictly enforced prior to face enrollment (`User.consent_biometric == True`). Face processing is blocked for accounts without active biometric consent.
- **🗑️ Biometric Opt-Out & Right to Deletion**: Students retain the capability to revoke biometric consent and trigger permanent hard deletion of all stored facial feature embeddings via `DELETE /api/v1/users/{id}/biometric-data`.
- **📝 Non-Biometric Manual Attendance Alternative**: Students who choose not to participate in biometric recognition are accommodated through manual roll-call check-in and faculty override endpoints (`POST /api/v1/attendance/mark` with `is_manual_override=True`).
- **🛡️ Ephemeral In-Memory Video Processing**: Video stream frames are decoded and processed strictly in-memory (RAM) and are **never persisted to disk**.
- **🔒 Fernet Authenticated Encryption at Rest**: Stored 512-d ArcFace facial feature vectors are encrypted before database storage using Cryptography Fernet (AES-128-CBC with HMAC-SHA256 authenticated encryption using a 256-bit PBKDF2-derived key).
- **🎯 Multi-Face ByteTrack Persistence**: Tracks student face bounding boxes seamlessly across video frames using IoU overlap matching and Hungarian algorithm linear assignment.
- **😴 3D Head Pose & Temporal EAR Drowsiness Engine**: Calculates 3D Head Pose (Yaw, Pitch, Roll via OpenCV `solvePnP`) and Eye Aspect Ratio (EAR). Triggers temporal alerts when eye closure exceeds 2.0 seconds (~15 consecutive frames).
- **📱 Device Distraction Detector**: Detects mobile phones and laptops and spatially associates distractions to the nearest student tracks.
- **💡 Explainable Visual Engagement Score (0.0 – 100.0%)**: Weighted composite signal aggregating Head Pose (35%), Eye State (30%), Detection Confidence (20%), and Device Distraction (15%).
- **⚡ Real-Time Redis Pub/Sub & WebSocket Telemetry**: Streams presence events, drowsiness alerts, device distractions, and engagement updates to live dashboards over WebSockets.
- **🖥️ React 18 + Vite Glassmorphism Frontend**: Features a Faculty Live Stream Dashboard with bounding box overlays, a Student Biometric Portal, and an Institutional Admin Console.

---

## 🏗️ System Architecture

```text
               +--------------------------------------------------+
               |  Classroom Camera / RTSP Stream / Webcams        |
               +------------------------+-------------------------+
                                        |
                                        v
+----------------------------------------------------------------------------------+
|                              AI Processing Service                               |
|  [StreamReader] -> [YOLOv8 / Cascade Detector] -> [ArcFace 512-d Extractor]     |
|  [ByteTrack Tracker] -> [HeadPose 3D] -> [EAR Drowsiness] -> [Device Detector]   |
+---------------------------------------+------------------------------------------+
                                        |
                                        v
+----------------------------------------------------------------------------------+
|                            Redis Pub/Sub Event Broker                             |
|           Channels: attendai:events:session:{id} | attendai:events:alerts:{id}   |
+---------------------------------------+------------------------------------------+
                                        |
                    +-------------------+-------------------+
                    |                                       |
                    v                                       v
+-----------------------+   +--------------------------------------+
|            FastAPI Backend            |   |       WebSocket Gateway Router       |
| PostgreSQL 15 (Fernet Encrypted DB)   |   |    GET /api/v1/ws/sessions/{id}     |
+-------------------+-------------------+   +-------------------+------------------+
                    |                                           |
                    +-------------------+-----------------------+
                                        |
                                        v
+----------------------------------------------------------------------------------+
|                     React 18 + Vite + TypeScript Frontend                        |
|   [Faculty Live Dashboard]   [Student Portal]   [Institutional Admin Console]     |
+----------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11
- Node.js 20+ & npm
- PostgreSQL 15 & Redis 7 (or Docker Compose)

### 1. Backend Setup
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r ../ai_service/requirements.txt

# Run FastAPI Server (Port 8080)
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# App will open at http://localhost:3000
```

### 3. Docker Compose Setup (Development)
```bash
# Spins up PostgreSQL, Redis, FastAPI Backend, AI Service, and Frontend
docker compose up --build -d
```

> **Security Note on Production Deployment**:
> In production environments (`APP_ENV=production`), the application enforces strict secret key validation at boot. Secure values of at least 32 characters must be supplied for `SECRET_KEY` and `JWT_SECRET_KEY`; any attempt to use default or insecure fallback values will halt startup.

---

## 🧪 Running the Verification Test Suite

AttendAI includes an automated test suite covering authentication, permissions, face detection, ArcFace recognition, AES-256 encryption, ByteTrack tracking, 3D head pose, EAR eye state, device detection, engagement scoring, Redis pub/sub, WebSockets, and reporting:

```bash
# From the project root
source backend/.venv/bin/activate
pytest
```

---

## 📊 End-to-End Benchmark Performance

Repeatable benchmark results executed via `ai_service/scripts/simulate_classroom.py`:

```text
-------------------------------------------------------
📊 REPEATABLE BENCHMARK RESULTS (3 RUNS, N = 90 FRAMES)
-------------------------------------------------------
 • Test Environment:        Apple Silicon (macOS), CPU inference
 • Execution Mode:          Headless pipeline with lightweight feature extractor
 • Iterations:              3 consecutive runs of 30 synthetic frames (N = 90 frames total)
 • Run 1:                   8.16 ms / frame (122.54 FPS, 0.245 s)
 • Run 2:                   6.80 ms / frame (147.14 FPS, 0.204 s)
 • Run 3:                   6.78 ms / frame (147.39 FPS, 0.204 s)
 -------------------------------------------------------
 • Mean Frame Latency:      ~7.25 ms / frame
 • Aggregate Throughput:    ~138 FPS (90 frames / 0.653 s total processing time)
 • Arithmetic Mean Rate:    ~139 FPS (arithmetic average of individual per-run FPS results)
-------------------------------------------------------
```
> **Throughput Measurement Distinction**:
> Aggregate throughput is calculated as total frames divided by total wall-clock processing time (90 frames / 0.653 s ≈ 137.82 FPS ≈ 138 FPS), distinguished from the arithmetic mean of individual per-run rates (139.02 FPS).
> **Note on Model Variations**:
> The above benchmark reflects CPU inference using the built-in lightweight feature extractor and tracker. Deployments utilizing full GPU-accelerated deep learning backends (YOLOv8 face/device detection and ArcFace ResNet-100 ONNX models) will exhibit different latency and throughput profiles depending on GPU compute capabilities, batch size, and video resolution.

---

## 🔒 Privacy Architecture & Data Governance

AttendAI implements technical privacy-by-design safeguards:

- **Explicit Opt-In**: Biometric enrollment requires explicit student consent recorded via `POST /api/v1/users/{id}/consent-biometric`. Unconsented accounts are excluded from facial recognition workflows.
- **Opt-Out & Erasure**: Students may withdraw biometric consent at any time. A dedicated deletion endpoint (`DELETE /api/v1/users/{id}/biometric-data`) purges encrypted facial vectors from the database.
- **Non-Biometric Alternative**: Institutions must support students who do not wish to use facial recognition. AttendAI provides manual roll-call override tools for faculty to record attendance independently.
- **Data Minimization & Ephemeral Video**: Video frames are processed in volatile memory (RAM) and immediately discarded. No camera footage or static images are written to persistent storage.
- **Encrypted Storage**: 512-dimensional facial feature vectors are stored as Fernet encrypted byte arrays (AES-128-CBC encryption with HMAC-SHA256 data integrity authentication).

> **Legal & Regulatory Notice**:
> This platform implements technical privacy controls and data minimization techniques as an engineering demonstration. It does not constitute formal compliance certification under GDPR, FERPA, BIPA, or other jurisdictional privacy regulations. Organizations planning deployment must perform independent legal and regulatory compliance reviews.

---

## 📜 Licensing & Third-Party Notices

AttendAI application source code is released under the **MIT License**. See the [LICENSE](LICENSE) file for complete terms.

### Third-Party & Upstream Model Disclosures
The MIT License covers only the original source code developed in this repository. It does not license or grant rights to third-party libraries, architectures, or pre-trained model weights:

- **Ultralytics YOLOv8**: Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0) or commercial license. AttendAI interacts with YOLOv8 via optional runtime imports with graceful heuristic fallbacks when not installed.
- **InsightFace / ArcFace**: InsightFace library code is MIT licensed; pre-trained ArcFace model weights are subject to non-commercial research restrictions set by their respective creators. No pre-trained model weights are bundled in this repository.
- **MediaPipe**: Licensed under the Apache License 2.0.
- **OpenCV**: Licensed under the Apache License 2.0.
