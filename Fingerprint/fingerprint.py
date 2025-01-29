
import os
import json
import getpass
import ctypes
import shutil
import time
from cryptography.fernet import Fernet
from Foundation import NSObject
from LocalAuthentication import LAContext, LAPolicyDeviceOwnerAuthenticationWithBiometrics

# Generate or load encryption key
def load_key():
    key_file = "key.key"
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, "wb") as keyfile:
            keyfile.write(key)
    else:
        with open(key_file, "rb") as keyfile:
            key = keyfile.read()
    return key

key = load_key()
cipher = Fernet(key)

# Encrypt data
def encrypt_data(data):
    return cipher.encrypt(data.encode()).decode()

# Decrypt data
def decrypt_data(encrypted_data):
    return cipher.decrypt(encrypted_data.encode()).decode()

# Authenticate via Touch ID
def authenticate_via_touch_id():
    context = LAContext.alloc().init()
    reason = "Authenticate to access the file."
    success_flag = [False]  # Mutable list to store result

    def callback(success, error):
        success_flag[0] = success

    context.evaluatePolicy_localizedReason_reply_(
        LAPolicyDeviceOwnerAuthenticationWithBiometrics,  # Use the correct constant
        reason,
        callback
    )

    # Wait until authentication completes
    timeout = 5  # Maximum wait time in seconds
    for _ in range(timeout * 10):
        if success_flag[0]:
            return True
        time.sleep(0.1)  # Wait a short period before checking again

    return False  # Return False if authentication does not complete in time

# Access secured file
def access_protected_file():
    filename = "Fingerprint/secure_file.txt"
    if authenticate_via_touch_id():
        print("Authentication successful! Opening file...")
        if os.path.exists(filename):
            with open(filename, "r") as f:
                print("File Contents:")
                print(f.read())
        else:
            print("File does not exist. Creating a new one.")
            with open(filename, "w") as f:
                f.write("This is a protected file.")
    else:
        print("Authentication failed!")

if __name__ == "__main__":
    access_protected_file()
