import time, hmac, hashlib, json
secret = "secret"
authobj = {
    'api_key': "MjkwYzc3MDI2MjhhNGZkNDg1MjJkODgyYjBmN2MyMTM4M",
    'upn': "joe@company.com",
    'timestamp': str(int(time.time() * 1000)),
    'signature_method': 'HMAC-SHA1',
    'api_version': '1.0'
}
hash = hmac.new(secret, digestmod=hashlib.sha1)
hash.update(authobj['api_key'] + authobj['upn'] + authobj['timestamp'])
authobj['signature'] = hash.hexdigest()
valid_json_auth_object = json.dumps(authobj)

def create_signature(secret, *parts):
    import hmac, hashlib
    hash = hmac.new(secret, digestmod=hashlib.sha1)
    for part in parts:
        hash.update(str(part))
    return hash.hexdigest()

