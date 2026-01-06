#!/bin/bash
# Sandbox Environment Reminder Hook
# Runs at session start to remind that this is a sandboxed environment

cat << 'EOF'
═══════════════════════════════════════════════════════════
🔒 SANDBOX ENVIRONMENT REMINDER
═══════════════════════════════════════════════════════════
⚠️  THIS IS A SANDBOXED WEB ENVIRONMENT

CRITICAL RULES:
• Packages do NOT persist between sessions
• NEVER tell user to install packages locally (pip install)
• Instead: Add dependencies to requirements.txt for CI
• Code must handle missing deps with try/except

✅ WHAT WORKS:
• GitHub API via curl with PAT
• Git operations
• File read/write
• Python scripts (with available deps only)

❌ WHAT DOESN'T PERSIST:
• pip install (resets each session)
• npm install (resets each session)
• Docker containers (not available)
• System packages (apt install)

💡 If a dependency is missing:
1. Add it to requirements.txt
2. CI will install it in GitHub Actions
3. Do NOT ask user to install locally
═══════════════════════════════════════════════════════════
EOF
