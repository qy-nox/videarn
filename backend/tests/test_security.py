from datetime import timedelta
from app.core.security import create_token, decode_token
def test_jwt_round_trip():
    token=create_token("user-id","access",timedelta(minutes=5))
    assert decode_token(token)["sub"]=="user-id"
