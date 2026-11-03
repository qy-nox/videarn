from base64 import b64decode
from urllib.parse import parse_qsl, urlencode
import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

GOOGLE_KEYS_URL = "https://www.gstatic.com/admob/reward/verifier-keys.json"

async def verify_ssv_signature(query: dict[str, str], client: httpx.AsyncClient | None = None) -> bool:
    signature = query.get("signature")
    key_id = query.get("key_id")
    if not signature or not key_id:
        return False
    payload = urlencode([(key, value) for key, value in query.items() if key != "signature"])
    owned = client is None
    client = client or httpx.AsyncClient(timeout=5)
    try:
        response = await client.get(GOOGLE_KEYS_URL)
        response.raise_for_status()
        key_data = next((item for item in response.json()["keys"] if str(item["keyId"]) == str(key_id)), None)
        if not key_data:
            return False
        public_key = serialization.load_pem_public_key(key_data["publicKey"].encode())
        public_key.verify(b64decode(signature), payload.encode(), padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False
    finally:
        if owned:
            await client.aclose()
