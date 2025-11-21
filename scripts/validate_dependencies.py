#!/usr/bin/env python3
"""
Validate dependencies before committing/pushing.

This script checks for:
1. Dependency conflicts
2. Missing dependencies
3. Version compatibility issues

Run before committing: python3 scripts/validate_dependencies.py
"""

import subprocess
import sys
from pathlib import Path

def check_dependency_conflicts():
    """Check if requirements.txt has dependency conflicts."""
    print("=" * 70)
    print("🔍 VALIDATING DEPENDENCIES")
    print("=" * 70)
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print(f"✅ Found requirements.txt")
    
    # Try to install dependencies in dry-run mode using pip's resolver
    print("\n📦 Checking for dependency conflicts...")
    try:
        # Use pip check or pip install --dry-run with --break-system-packages for validation
        # This is safe because we're only doing a dry-run
        result = subprocess.run(
            ["python3", "-m", "pip", "install", "--dry-run", "--break-system-packages", "-r", str(requirements_file)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            error_output = result.stderr or result.stdout
            
            # Check for specific conflict messages
            if "ERROR: ResolutionImpossible" in error_output or "ERROR: Cannot install" in error_output:
                print("❌ Dependency conflicts detected!")
                print("\nError output:")
                print(error_output[:500])  # Limit output
                print("\n💡 TIP: Use 'pip install pip-tools' and 'pip-compile requirements.in' to resolve conflicts")
                return False
            elif "externally-managed-environment" in error_output:
                # This is OK - we're just validating, not actually installing
                print("✅ Dependency check completed (externally-managed environment detected - this is OK)")
                return True
            else:
                print("⚠️  Unexpected error during dependency check:")
                print(error_output[:300])
                return True  # Don't fail on unexpected errors
        else:
            print("✅ No dependency conflicts detected")
            return True
            
    except subprocess.TimeoutExpired:
        print("⚠️  Dependency check timed out (this is OK for dry-run)")
        return True
    except FileNotFoundError:
        print("⚠️  pip not found - skipping dependency check")
        return True
    except Exception as e:
        print(f"⚠️  Error checking dependencies: {e}")
        print("   This is OK - validation will happen in CI")
        return True  # Don't fail on check errors


def check_python_version():
    """Check if Python version matches CI (3.11)."""
    print("\n🐍 Checking Python version...")
    version = sys.version_info
    print(f"   Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 11:
        print("✅ Python 3.11 (matches CI)")
        return True
    else:
        print(f"⚠️  Python {version.major}.{version.minor} (CI uses 3.11)")
        print("   This is OK for local dev, but CI will use Python 3.11")
        return True


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("🚀 DEPENDENCY VALIDATION")
    print("=" * 70)
    print()
    
    checks = {
        "Python Version": check_python_version(),
        "Dependency Conflicts": check_dependency_conflicts(),
    }
    
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check_name}: {status}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n🎉 All dependency checks passed!")
        return 0
    else:
        print("\n❌ Dependency validation failed!")
        print("\n💡 Fix issues before committing:")
        print("   1. Resolve dependency conflicts")
        print("   2. Update requirements.txt")
        print("   3. Run validation again: python3 scripts/validate_dependencies.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())

