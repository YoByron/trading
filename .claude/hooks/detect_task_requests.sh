#!/bin/bash
# .claude/hooks/detect_task_requests.sh
# Detects when CEO is giving CTO a task and reminds about Task agent usage

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract prompt using jq (with fallback if jq not available)
if command -v jq &> /dev/null; then
    PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')
else
    # Fallback: basic grep extraction
    PROMPT=$(echo "$INPUT" | grep -o '"prompt":"[^"]*"' | cut -d'"' -f4 || echo "")
fi

# Exit if no prompt extracted
if [ -z "$PROMPT" ]; then
    exit 0
fi

# Convert to lowercase for case-insensitive matching
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

# Define task-triggering patterns
TASK_KEYWORDS=(
    "implement"
    "create"
    "build"
    "fix"
    "add"
    "refactor"
    "update"
    "write"
    "develop"
    "deploy"
    "setup"
    "configure"
    "integrate"
    "migrate"
    "optimize"
    "enhance"
    "modify"
    "change"
    "make"
    "generate"
    "install"
    "remove"
    "delete"
)

# Define question patterns (to avoid false positives)
QUESTION_PATTERNS=(
    "what is"
    "what's"
    "how do"
    "how does"
    "why"
    "can you explain"
    "tell me about"
    "show me"
    "what are"
    "describe"
)

# Check if prompt is a question
IS_QUESTION=false
for pattern in "${QUESTION_PATTERNS[@]}"; do
    if [[ "$PROMPT_LOWER" == *"$pattern"* ]]; then
        IS_QUESTION=true
        break
    fi
done

# Check for task keywords
TASK_DETECTED=false
if [ "$IS_QUESTION" = false ]; then
    for keyword in "${TASK_KEYWORDS[@]}"; do
        if [[ "$PROMPT_LOWER" == *"$keyword"* ]]; then
            TASK_DETECTED=true
            break
        fi
    done
fi

# Additional heuristics for task detection
if [ "$IS_QUESTION" = false ] && [ "$TASK_DETECTED" = false ]; then
    # Check for imperative sentence patterns (commands without question marks)
    if [[ ! "$PROMPT" == *"?"* ]] && [[ ${#PROMPT} -gt 20 ]]; then
        # Check for command-like structure (verb at start)
        FIRST_WORD=$(echo "$PROMPT" | awk '{print tolower($1)}')
        case "$FIRST_WORD" in
            go|run|execute|start|stop|test|debug|check|verify|ensure|let|please)
                TASK_DETECTED=true
                ;;
        esac
    fi

    # Check for multi-step indicators
    if [[ "$PROMPT_LOWER" == *"then"* ]] || \
       [[ "$PROMPT_LOWER" == *"and then"* ]] || \
       [[ "$PROMPT_LOWER" == *"after that"* ]] || \
       [[ "$PROMPT" == *"1."* ]] || \
       [[ "$PROMPT" == *"2."* ]]; then
        TASK_DETECTED=true
    fi
fi

# Output reminder if task detected
if [ "$TASK_DETECTED" = true ]; then
    cat << 'EOF'

⚡ TASK DETECTED - PARALLELIZATION REMINDER ⚡

Per CLAUDE.md MASSIVE PARALLELIZATION MANDATE:

🎯 3-Phase Protocol:
  Phase 1: RESEARCH - Use subagents for discovery (parallel file searches, code exploration)
  Phase 2: PLANNING - Identify parallelization opportunities
  Phase 3: IMPLEMENTATION - Launch multiple Task agents simultaneously

⚡ Execution Requirements:
  • Use Anthropic Agent SDK (Task tool) for ALL significant work
  • Spawn parallel agents IMMEDIATELY - don't work sequentially
  • Each agent works independently on separate subtasks
  • Coordinate results via Agent SDK orchestration

💡 Ask Yourself:
  • Can I break this into 2-5 parallel subtasks?
  • Which parts are independent and can run simultaneously?
  • Am I using agents for maximum velocity?

🚫 FORBIDDEN: "You need to..." or "Manual steps required..."
✅ REQUIRED: DO IT YOURSELF with parallel agents

EOF
fi

# Always exit 0 to allow prompt to continue (just adding context)
exit 0
