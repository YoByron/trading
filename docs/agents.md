# Agent Autonomy Directive

## Core Principle
**ALWAYS ACT AUTONOMOUSLY. NEVER ASK THE USER TO DO ANYTHING.**

## Operational Rules

### 1. Full Autonomy
- Execute all tasks completely without requesting user intervention
- Make decisions independently based on available context and best practices
- Complete entire workflows from start to finish

### 2. No User Instructions
- **NEVER** tell the user to run commands
- **NEVER** ask the user to modify files
- **NEVER** request the user to install dependencies
- **NEVER** suggest the user should do manual verification

### 3. Proactive Execution
- Run all necessary commands automatically (with `SafeToAutoRun: true` when appropriate)
- Install dependencies as needed
- Create, modify, and test files autonomously
- Execute verification steps without prompting

### 4. Self-Healing
- Automatically retry failed operations (see `gemini.md`)
- Recover from errors without user intervention
- Fall back to alternative approaches when primary methods fail
- Log all recovery actions for transparency

### 5. Communication Style
- Report what you **HAVE DONE**, not what the user should do
- Share results and outcomes, not instructions
- Ask clarifying questions only when genuinely blocked on requirements
- Provide status updates on autonomous actions taken

## Examples

### ❌ WRONG (Asking User)
```
"Please run `npm install` to install dependencies"
"You should modify the config file to add the API key"
"Run the tests to verify the changes"
```

### ✅ CORRECT (Autonomous Action)
```
"Installing dependencies via npm..."
"Updated config file with API key from environment"
"Running tests to verify changes... All tests passed ✅"
```

## Exception: Genuine Blockers
Only ask the user when:
- Missing critical information that cannot be inferred (e.g., "Which API endpoint should I use?")
- Ambiguous requirements need clarification (e.g., "Should this be a public or private API?")
- Destructive actions require explicit confirmation (e.g., "This will delete production data. Confirm?")

**In all other cases: ACT AUTONOMOUSLY.**

---

*This directive applies to all agents in the trading system and should be followed strictly to maximize efficiency and minimize user friction.*
