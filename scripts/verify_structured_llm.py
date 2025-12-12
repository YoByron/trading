import os
import sys

from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())
load_dotenv()

try:
    from src.core.structured_output_client import StructuredLLMClient

    # Check simple instantiation
    print("✅ Classes imported successfully")

    client = StructuredLLMClient(client=None, model="test")  # type: ignore
    print("✅ Client instantiated")

    print("✅ Verification passed")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
