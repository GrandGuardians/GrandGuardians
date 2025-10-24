"""AES-256-GCM 加/解密模块，兼容 gui.py

接口：
    encrypt(password: str, plaintext: str) -> str
    decrypt(password: str, token: str) -> str
    命令行：encrypt/decrypt/demo
"""
import base64
import os
import sys
import argparse
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception as e:
    raise ImportError("缺少依赖：请先 pip install cryptography") from e

def _derive_key(password: str, salt: bytes, iterations: int = 200_000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode("utf-8"))

def encrypt(password: str, plaintext: str) -> str:
    if not isinstance(plaintext, str):
        raise TypeError("plaintext 必须是 str 类型")
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    token = salt + nonce + ciphertext
    return base64.b64encode(token).decode("utf-8")

def decrypt(password: str, token: str) -> str:
    try:
        data = base64.b64decode(token)
    except Exception as exc:
        raise ValueError("token 不是有效的 base64 数据") from exc
    if len(data) < 16 + 12 + 16:
        raise ValueError("token 数据太短，无法解析")
    salt = data[:16]
    nonce = data[16:28]
    ciphertext = data[28:]
    key = _derive_key(password, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("解密失败（密码错误或数据被篡改）") from exc
    return plaintext_bytes.decode("utf-8")

def _demo():
    samples = [
        "Hello, world!",
        "你好，世界！",
        "Testing 中英 mixed: 这是一个测试 123",
    ]
    password = "CorrectHorseBatteryStaple"
    print("运行内置自测：")
    for i, s in enumerate(samples, 1):
        token = encrypt(password, s)
        recovered = decrypt(password, token)
        ok = "OK" if recovered == s else "FAIL"
        print(f"样例 {i}: {ok}")
        print(f" 原文: {s}")
        print(f" Token(base64): {token[:60]}... ")
        print(f" 解出: {recovered}")
        print("-")
    try:
        decrypt("wrong-password", encrypt(password, samples[0]))
    except ValueError:
        print("错误密码检测：OK（抛出解密失败）")
    else:
        print("错误密码检测：FAIL（意外通过）")
        return 2
    return 0

def _cli():
    parser = argparse.ArgumentParser(description="基于密码的 AES-256-GCM 加/解密工具（支持中文/英文）。")
    sub = parser.add_subparsers(dest="cmd")
    p_enc = sub.add_parser("encrypt", help="加密字符串")
    p_enc.add_argument("password", help="用于派生密钥的密码")
    p_enc.add_argument("input", help="要加密的字符串")
    p_dec = sub.add_parser("decrypt", help="解密 token（base64）到明文")
    p_dec.add_argument("password", help="用于派生密钥的密码")
    p_dec.add_argument("token", help="要解密的 base64 token")
    p_demo = sub.add_parser("demo", help="运行内置自测，演示中英混合加解密")
    args = parser.parse_args()
    if args.cmd == "encrypt":
        token = encrypt(args.password, args.input)
        print(token)
    elif args.cmd == "decrypt":
        plaintext = decrypt(args.password, args.token)
        print(plaintext)
    elif args.cmd == "demo":
        rc = _demo()
        sys.exit(rc)
    else:
        parser.print_help()

if __name__ == "__main__":
    _cli()
