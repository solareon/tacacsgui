#!/usr/bin/env python3
import os
import base64
import hashlib
import argparse
import getpass

def generate_salt() -> str:
    # crypt.METHOD_SHA512 salts are exactly 16 chars using './A-Za-z0-9'. Swap out deprecated crypt with random/b64
    random_bytes = os.urandom(12)  # 12 bytes = 16 chars in base64
    salt = base64.b64encode(random_bytes, altchars=b'./').decode('utf-8')
    return salt

def generate_digest(secret_bytes: bytes, salt_bytes: bytes, rounds: int|None=None) -> bytes:
    if rounds is None:
        rounds = 5000
    digest = hashlib.pbkdf2_hmac('sha512', secret_bytes, salt_bytes, rounds, dklen=16)
    return digest

def generate_hash(password, salt=None, rounds=100000) -> str:

    if salt == None:
        salt = generate_salt()
    run_salt_bytes = salt.encode('utf8')
    run_digest_bytes = generate_digest(password.encode('utf8'),
                                 salt_bytes=run_salt_bytes,
                                 rounds=rounds)
    return (f"$sha512"
          f"${rounds}"
          f"${base64.b64encode(run_salt_bytes).decode('utf8')}"
          f"${base64.b64encode(run_digest_bytes).decode('utf8')}")
    
def verify_hash(password, hash):
    try:
        # Expect format: $sha512$<rounds>$<salt_b64>$<digest_b64>
        parts = hash.split('$')
        if len(parts) != 5 or parts[1] != 'sha512':
            return False
        rounds = int(parts[2])
        salt_b64 = parts[3]
        salt = base64.b64decode(salt_b64)
        # Use generate_digest instead of direct pbkdf2_hmac
        run_digest_bytes = generate_digest(password.encode('utf8'), salt, rounds=rounds)
        hash_bytes = (f"$sha512${rounds}${salt_b64}${base64.b64encode(run_digest_bytes).decode('utf8')}")
        
        return hash_bytes == hash
    except Exception:
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a PBKDF2-SHA512 hash for ASA')
    parser.add_argument('--secret', type=str, default=None,
                        help='The secret to encode (may be saved to shell history.)')
    parser.add_argument('--salt', type=str, default=None,
                        help='Hardcoded salt to use. If not specified, a random salt will be generated')
    parser.add_argument('--rounds', type=int, default=5000,
                        help='The number of rounds to use')
    args = parser.parse_args()

    if args.secret is None:
        args.secret = getpass.getpass('Enter secret to encode: ')
    if args.salt is None:
        args.salt = generate_salt()
        run_salt_bytes = args.salt.encode('utf8')
    else:
        run_salt_bytes = base64.b64decode(args.salt.strip())

    run_digest_bytes = generate_digest(args.secret.encode('utf8'),
                                 salt_bytes=run_salt_bytes,
                                 rounds=args.rounds)
    print(f"$sha512"
          f"${args.rounds}"
          f"${base64.b64encode(run_salt_bytes).decode('utf8')}"
          f"${base64.b64encode(run_digest_bytes).decode('utf8')}")
