import hashlib

def calculate_md5(string: str):
    md5_hash = hashlib.md5(string.encode())
    md5 = md5_hash.hexdigest()
    return md5
