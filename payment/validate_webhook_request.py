import base64
import hashlib
import ecdsa
import requests
import logging
from config.config import MONOBANK_API_BASEURL, MONOBANK_API_KEY

# ========================================================

def fetch_public_key():
    url = MONOBANK_API_BASEURL+"merchant/pubkey"
    headers = {
        "X-Token": MONOBANK_API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("key")
    else:
        raise Exception(f"Failed to fetch public key: {response.status_code} - {response.text}")

# ========================================================

def validate_request(x_sign_base64, body_bytes):
    try:
        pub_key_base64 = fetch_public_key()

        pub_key_bytes = base64.b64decode(pub_key_base64)
        signature_bytes = base64.b64decode(x_sign_base64)
        pub_key = ecdsa.VerifyingKey.from_pem(pub_key_bytes.decode())

        ok = pub_key.verify(signature_bytes, body_bytes, sigdecode=ecdsa.util.sigdecode_der, hashfunc=hashlib.sha256)
        logging.info(f"Validate_request validation result: {ok}")
        
        return ok
    except Exception as e:
        logging.error(f"Validation error: {e}")
        return False