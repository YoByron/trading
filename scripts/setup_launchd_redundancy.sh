#!/bin/bash
# Setup launchd daemons as backup/redundancy for GitHub Actions workflows
# These will only run if GitHub Actions didn't execute successfully

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LAUNCHD_DIR="${HOME}/Library/LaunchAgents"

echo "🔧 Setting up launchd redundancy for GitHub Actions workflows..."
echo ""

# Create LaunchAgents directory if it doesn't exist
mkdir -p "${LAUNCHD_DIR}"

# Function to create or update a plist
create_plist() {
    local label=$1
    local script=$2
    local schedule=$3
    local plist_file="${LAUNCHD_DIR}/${label}.plist"

    echo "📝 Creating ${label}.plist..."

    cat > "${plist_file}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${label}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${script}</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${REPO_ROOT}</string>

    <key>StandardOutPath</key>
    <string>${REPO_ROOT}/logs/launchd_${label}_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${REPO_ROOT}/logs/launchd_${label}_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>KeepAlive</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${HOME}/.local/bin</string>
        <key>HOME</key>
        <string>${HOME}</string>
    </dict>

    ${schedule}
</dict>
</plist>
EOF

    echo "✅ Created ${plist_file}"
}

# 1. Daily Trading (backup for GitHub Actions daily-trading.yml)
echo "1️⃣  Setting up daily trading redundancy..."
create_plist "com.trading.autonomous.backup" \
    "${REPO_ROOT}/scripts/autonomous_trader_with_redundancy.sh" \
    '<key>StartCalendarInterval</key>
    <array>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>40</integer></dict>
        <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>40</integer></dict>
        <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>40</integer></dict>
        <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>40</integer></dict>
        <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>40</integer></dict>
    </array>'

# 2. Health Check (backup for GitHub Actions health checks)
echo ""
echo "2️⃣  Setting up health check redundancy..."
cat > "${LAUNCHD_DIR}/com.trading.healthcheck.backup.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.healthcheck.backup</string>

    <key>ProgramArguments</key>
    <array>
        <string>${REPO_ROOT}/venv/bin/python3</string>
        <string>${REPO_ROOT}/scripts/health_check.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${REPO_ROOT}</string>

    <key>StandardOutPath</key>
    <string>${REPO_ROOT}/logs/launchd_com.trading.healthcheck.backup_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${REPO_ROOT}/logs/launchd_com.trading.healthcheck.backup_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>KeepAlive</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${HOME}/.local/bin</string>
        <key>HOME</key>
        <string>${HOME}</string>
    </dict>

    <key>StartCalendarInterval</key>
    <array>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>10</integer></dict>
        <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>10</integer></dict>
        <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>10</integer></dict>
        <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>10</integer></dict>
        <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>10</integer></dict>
    </array>
</dict>
</plist>
EOF
echo "✅ Created ${LAUNCHD_DIR}/com.trading.healthcheck.backup.plist"

# 3. Dashboard Update (backup for GitHub Actions dashboard-auto-update.yml)
echo ""
echo "3️⃣  Setting up dashboard update redundancy..."
cat > "${LAUNCHD_DIR}/com.trading.dashboard.backup.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trading.dashboard.backup</string>

    <key>ProgramArguments</key>
    <array>
        <string>${REPO_ROOT}/venv/bin/python3</string>
        <string>${REPO_ROOT}/scripts/generate_progress_dashboard.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${REPO_ROOT}</string>

    <key>StandardOutPath</key>
    <string>${REPO_ROOT}/logs/launchd_com.trading.dashboard.backup_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>${REPO_ROOT}/logs/launchd_com.trading.dashboard.backup_stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>KeepAlive</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${HOME}/.local/bin</string>
        <key>HOME</key>
        <string>${HOME}</string>
    </dict>

    <key>StartCalendarInterval</key>
    <array>
        <dict><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>
    </array>
</dict>
</plist>
EOF
echo "✅ Created ${LAUNCHD_DIR}/com.trading.dashboard.backup.plist"

echo ""
echo "✅ All launchd plists created!"
echo ""
echo "📋 Next steps:"
echo "   1. Review the plists in: ${LAUNCHD_DIR}/"
echo "   2. Load them with:"
echo "      launchctl load ${LAUNCHD_DIR}/com.trading.autonomous.backup.plist"
echo "      launchctl load ${LAUNCHD_DIR}/com.trading.healthcheck.backup.plist"
echo "      launchctl load ${LAUNCHD_DIR}/com.trading.dashboard.backup.plist"
echo ""
echo "   3. Check status:"
echo "      launchctl list | grep trading"
echo ""
echo "   4. View logs:"
echo "      tail -f ${REPO_ROOT}/logs/launchd_*.log"
echo ""
echo "🎯 These daemons will ONLY run if GitHub Actions didn't execute successfully!"
