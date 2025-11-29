# 📱 iPhone Access Guide

Access your trading dashboards from your iPhone on the same local network.

## Quick Start

### Option 1: Launch Scripts (Easiest)

The launch scripts now automatically detect your Mac's IP address:

```bash
# Trading Control Center Dashboard
./scripts/launch_trading_dashboard.sh

# Sentiment RAG Dashboard
./launch_dashboard.sh
```

The script will display:
- **Local access**: `http://localhost:8501`
- **iPhone access**: `http://192.168.x.x:8501` (your Mac's IP)

### Option 2: Manual Launch

```bash
# Activate virtual environment
source venv/bin/activate

# Launch with network access enabled
streamlit run dashboard/trading_dashboard.py --server.address=0.0.0.0 --server.port=8501
```

## Finding Your Mac's IP Address

### Method 1: From Terminal
```bash
# WiFi connection
ipconfig getifaddr en0

# Ethernet connection
ipconfig getifaddr en1
```

### Method 2: From System Settings
1. Open **System Settings** → **Network**
2. Select your active connection (Wi-Fi or Ethernet)
3. Your IP address is shown (e.g., `192.168.1.100`)

## Accessing from iPhone

1. **Ensure both devices are on the same Wi-Fi network**
2. **Launch the dashboard** on your Mac using one of the scripts above
3. **Open Safari on your iPhone**
4. **Enter the URL**: `http://YOUR_MAC_IP:8501`
   - Example: `http://192.168.1.100:8501`
5. **Bookmark it** for easy access!

## Security Notes

⚠️ **Important**: The dashboard is only accessible on your local network. For security:

- ✅ **Safe**: Accessing from iPhone on same Wi-Fi (private network)
- ❌ **Not recommended**: Exposing to public internet without authentication
- 🔒 **Production**: Use Streamlit Cloud or add authentication for public access

## Troubleshooting

### Can't Connect from iPhone

1. **Check firewall**: macOS Firewall might be blocking connections
   ```bash
   # Allow Streamlit through firewall
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/venv/bin/streamlit
   ```

2. **Verify same network**: Both devices must be on the same Wi-Fi

3. **Check IP address**: Make sure you're using the correct IP (en0 for Wi-Fi)

4. **Try different port**: If 8501 is busy, use another port:
   ```bash
   streamlit run dashboard/trading_dashboard.py --server.address=0.0.0.0 --server.port=8502
   ```

### Firewall Settings (macOS)

1. Open **System Settings** → **Network** → **Firewall**
2. Click **Options**
3. Ensure **Block all incoming connections** is **OFF**
4. Add Streamlit to allowed apps if needed

## Cloud Deployment (Public Access)

For access from anywhere (not just local network), deploy to:

### Streamlit Cloud (Free & Easiest)
1. Push code to GitHub
2. Connect repo at [share.streamlit.io](https://share.streamlit.io)
3. Deploy automatically
4. Access from anywhere via public URL

### Docker on Cloud Server
- Deploy using `docker-compose.yml` to AWS, DigitalOcean, etc.
- Access via public IP or domain name

## Mobile Features

The dashboards are mobile-responsive:
- ✅ Touch-friendly navigation
- ✅ Responsive charts and tables
- ✅ Vertical stacking on small screens
- ✅ Auto-resizing components

## Available Dashboards

1. **Trading Control Center** (`trading_dashboard.py`)
   - Real-time performance metrics
   - Current positions
   - Risk management status
   - Recent trades

2. **Sentiment RAG Dashboard** (`sentiment_dashboard.py`)
   - Sentiment analysis visualization
   - Historical trends
   - Trade impact analysis
   - Data sources overview

## Quick Reference

```bash
# Get Mac IP address
ipconfig getifaddr en0

# Launch Trading Dashboard (network-enabled)
streamlit run dashboard/trading_dashboard.py --server.address=0.0.0.0 --server.port=8501

# Launch Sentiment Dashboard (network-enabled)
streamlit run dashboard/sentiment_dashboard.py --server.address=0.0.0.0 --server.port=8501
```

---

**Pro Tip**: Add the dashboard URL to your iPhone's home screen for app-like access:
1. Open dashboard in Safari
2. Tap Share button
3. Select "Add to Home Screen"
