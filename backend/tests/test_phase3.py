from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from urllib.parse import urlencode
import base64
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from app.api.v1.wallet import withdrawal_rule
from app.services.economy import DEFAULT_ECONOMY
from app.services.ssv import verify_ssv_signature

def test_withdrawal_requires_phone_and_age():
    economy = DEFAULT_ECONOMY
    user = SimpleNamespace(phone_verified=False, created_at=datetime.now(timezone.utc) - timedelta(days=30))
    with pytest.raises(ValueError, match="Phone"):
        withdrawal_rule(user, Decimal("2"), "bank", economy)
    user.phone_verified = True
    user.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ValueError, match="7 days"):
        withdrawal_rule(user, Decimal("2"), "bank", economy)

def test_withdrawal_converts_currency_to_coins():
    user = SimpleNamespace(phone_verified=True, created_at=datetime.now(timezone.utc) - timedelta(days=8))
    assert withdrawal_rule(user, Decimal("2.50"), "bank", DEFAULT_ECONOMY) == 2500

class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): return None
    def json(self): return self.payload

class FakeClient:
    def __init__(self, response): self.response = response
    async def get(self, _url): return self.response

@pytest.mark.asyncio
async def test_ssv_signature_verification():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    query = {"ad_network": "test", "ad_unit": "unit", "custom_data": "user", "transaction_id": "tx", "key_id": "7"}
    payload = urlencode(query).encode()
    query["signature"] = base64.b64encode(private.sign(payload, padding.PKCS1v15(), hashes.SHA256())).decode()
    client = FakeClient(FakeResponse({"keys": [{"keyId": 7, "publicKey": public}]}))
    assert await verify_ssv_signature(query, client)
    query["transaction_id"] = "tampered"
    assert not await verify_ssv_signature(query, client)
