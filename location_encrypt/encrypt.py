from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import hashlib
import uuid

def hash(file_data):
    # file data in bytes
    salt = str(uuid.uuid4())
    hash_result = hashlib.sha512(file_data + salt.encode()).hexdigest()
    return hash_result, salt

def check_hash(file_data, salt):
    salt = str(salt)
    check_hash_result = hashlib.sha512(file_data + salt.encode()).hexdigest()
    return check_hash_result

def generate_symmetric_key():
    symmetric_key_raw = Fernet.generate_key().decode()
    symmetric_key = Fernet(symmetric_key_raw)
    return symmetric_key, symmetric_key_raw

def symmetric_encrypt(filename, key):
    with open(filename, "rb") as file:
        file_data = file.read()
    encrypted_data = key.encrypt(file_data)
    with open(filename, "wb") as file:
        file.write(encrypted_data)

def symmetric_decrypt(filename, key):
    with open(filename, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = key.decrypt(encrypted_data)
    with open(filename, "wb") as file:
        file.write(decrypted_data)

def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    with open('keys/private_key.pem', 'wb') as f:
        f.write(pem)

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open('keys/public_key.pem', 'wb') as f:
        f.write(pem)

def open_private_rsa_key():
    with open("keys/private_key.pem", "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
    return private_key

def open_public_rsa_key():
    with open("keys/public_key.pem", "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )
    return public_key

def open_file(filename):
    f = open(filename, 'rb')
    file_data = f.read()
    f.close()
    return file_data

def save_encrypted_file(filename, encrypted):
    f = open(filename, 'wb')
    f.write(encrypted)
    f.close()

def save_decrypted_file(filename, decrypted):
    f = open(filename, 'wb')
    f.write(decrypted)
    f.close()

def encrypt_rsa(message):
    encrypted = open_public_rsa_key().encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None
            )
        )
    return encrypted

def decrypt_rsa(encrypted):
    original_message = open_private_rsa_key().decrypt(
            encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None
            )
        )
    return original_message

