# 🔒 Security Guidelines

**Last Updated**: November 21, 2025  
**Purpose**: Prevent sensitive data exposure in code, logs, and output

---

## 🚨 Critical Rules

### 1. **NEVER Log Full API Keys or Secrets**

❌ **WRONG:**
```python
print(f"API Key: {api_key}")
print(f"API Key: {api_key[:20]}...")  # Still too much!
logger.info(f"Secret: {secret}")
```

✅ **CORRECT:**
```python
from src.utils.security import mask_api_key

print(f"API Key: {mask_api_key(api_key)}")  # Shows only first 4 chars
logger.info(f"Secret: {mask_api_key(secret)}")
```

### 2. **Use Security Utility Functions**

Always use `src.utils.security.mask_api_key()` or `mask_secret()`:

```python
from src.utils.security import mask_api_key, mask_secret

# Mask API keys (shows first 4 chars)
masked = mask_api_key(os.getenv("GOOGLE_API_KEY"))
print(f"✅ API Key found: {masked}")  # Output: "sk-1***"

# Mask secrets (shows first 4 chars)
masked = mask_secret(os.getenv("ALPACA_SECRET_KEY"))
print(f"✅ Secret found: {masked}")  # Output: "ABCD***"
```

### 3. **Maximum Visible Characters: 4**

- ✅ **Safe**: Show first 4 characters max
- ❌ **Unsafe**: Showing 10+ characters
- ❌ **Critical**: Showing full key

### 4. **Pre-Commit Security Check**

A pre-commit hook automatically checks for security violations:

```bash
# Hook runs automatically on git commit
# Blocks commits with security violations
```

**What it checks:**
- API key slicing with more than 4 chars (`[:10]`, `[:20]`, etc.)
- Direct printing/logging of API keys
- Common sensitive data patterns

---

## 📋 Common Patterns to Avoid

### ❌ Bad Patterns

```python
# Too many characters visible
print(f"Key: {api_key[:10]}...")
print(f"Key: {api_key[:20]}...")

# Direct exposure
print(f"Key: {api_key}")
logger.debug(f"Secret: {secret}")

# In error messages
except Exception as e:
    logger.error(f"Failed with key: {api_key}")  # DANGEROUS!
```

### ✅ Good Patterns

```python
from src.utils.security import mask_api_key, sanitize_log_message

# Proper masking
print(f"Key: {mask_api_key(api_key)}")  # Shows "ABCD***"

# Sanitize log messages
message = f"API call failed with key: {api_key}"
logger.error(sanitize_log_message(message))  # Auto-masks keys

# Environment checks
if not api_key:
    print("❌ API key not configured")
else:
    print(f"✅ API key configured: {mask_api_key(api_key)}")
```

---

## 🔍 Security Audit Checklist

Before committing code, verify:

- [ ] No API keys printed/logged in full
- [ ] No secrets exposed in error messages
- [ ] Using `mask_api_key()` for all key displays
- [ ] Pre-commit hook passes
- [ ] No sensitive data in test output
- [ ] Environment variables loaded from `.env` (not hardcoded)

---

## 🛠️ Security Utility Functions

### `mask_api_key(api_key, visible_chars=4)`

Masks an API key, showing only first N characters.

```python
from src.utils.security import mask_api_key

masked = mask_api_key("sk-1234567890abcdef")
# Returns: "sk-1***"
```

### `mask_secret(secret, visible_chars=4)`

Masks a secret key, showing only first N characters.

```python
from src.utils.security import mask_secret

masked = mask_secret("ABCD1234EFGH5678")
# Returns: "ABCD***"
```

### `sanitize_log_message(message)`

Automatically detects and masks API keys/secrets in log messages.

```python
from src.utils.security import sanitize_log_message

message = "API call failed: api_key=sk-1234567890"
sanitized = sanitize_log_message(message)
# Returns: "API call failed: api_key=***"
```

### `is_sensitive_key(key_name)`

Checks if a variable name indicates sensitive data.

```python
from src.utils.security import is_sensitive_key

is_sensitive_key("api_key")  # True
is_sensitive_key("username")  # False
```

---

## 🚨 GitHub Code Scanning

GitHub CodeQL automatically scans for security issues:

- **Alert**: "Clear-text logging of sensitive information"
- **Severity**: High
- **Action**: Fix immediately using `mask_api_key()`

**Current Status**: ✅ All alerts fixed (Nov 21, 2025)

---

## 📚 Examples

### Example 1: Test Script

```python
#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from src.utils.security import mask_api_key

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY not found")
    sys.exit(1)

# ✅ CORRECT: Mask the key
print(f"✅ GOOGLE_API_KEY found: {mask_api_key(api_key)}")
```

### Example 2: Error Handling

```python
try:
    # API call
    result = api_client.call(api_key)
except Exception as e:
    # ✅ CORRECT: Don't expose key in error
    logger.error(f"API call failed: {e}")
    # ❌ WRONG: logger.error(f"API call failed with key {api_key}: {e}")
```

### Example 3: Configuration Validation

```python
from src.utils.security import mask_api_key

def validate_config():
    api_key = os.getenv("API_KEY")
    if api_key:
        print(f"✅ API Key configured: {mask_api_key(api_key)}")
    else:
        print("❌ API Key not configured")
```

---

## 🔗 Related Files

- `src/utils/security.py` - Security utility functions
- `.git/hooks/pre-commit-security-check` - Pre-commit security hook
- `docs/SECURITY_GUIDELINES.md` - This file

---

**Remember**: When in doubt, mask it! Better safe than sorry.

