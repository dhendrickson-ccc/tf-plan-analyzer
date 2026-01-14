#!/usr/bin/env python3
"""
Salt Manager for Terraform Plan Obfuscation

Handles cryptographic salt generation, encryption, storage, and retrieval
for deterministic sensitive value obfuscation.

Uses Fernet symmetric encryption with TF_ANALYZER_SALT_KEY environment variable
for portable salt storage across CI/CD nodes.
"""

import os
import sys
import secrets
import struct
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Tuple


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key from TF_ANALYZER_SALT_KEY environment variable.
    
    If the environment variable is not set, generates a new key and displays
    prominent security warnings to the user.
    
    Returns:
        bytes: Fernet encryption key (base64-encoded bytes, ready for Fernet())
    """
    key_b64 = os.environ.get('TF_ANALYZER_SALT_KEY')
    
    if key_b64:
        # Key is provided, return as bytes (it's already base64-encoded)
        return key_b64.encode('utf-8') if isinstance(key_b64, str) else key_b64
    
    # Generate new key and warn user to save it
    key = Fernet.generate_key()
    
    print("=" * 70, file=sys.stderr)
    print("WARNING: TF_ANALYZER_SALT_KEY environment variable not set!", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("Generated new encryption key (save this securely):", file=sys.stderr)
    print(f"\n  export TF_ANALYZER_SALT_KEY={key.decode()}\n", file=sys.stderr)
    print("SECURITY WARNINGS:", file=sys.stderr)
    print("  - Store this key in a secure location (password manager, CI secrets)", file=sys.stderr)
    print("  - DO NOT commit this key to version control", file=sys.stderr)
    print("  - This key will be visible in terminal history and CI logs", file=sys.stderr)
    print("  - Without this key, you cannot decrypt/reuse the salt file", file=sys.stderr)
    print("  - For CI/CD: Store in GitHub Secrets, GitLab CI variables, etc.", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    return key


def generate_salt() -> bytes:
    """
    Generate a cryptographically secure random salt.
    
    Uses secrets.token_bytes() for CSPRNG (cryptographically secure
    pseudo-random number generator).
    
    Returns:
        bytes: 32-byte (256-bit) random salt
    """
    return secrets.token_bytes(32)


def generate_position_seed() -> bytes:
    """
    Generate a random seed for salt position determination.
    
    This seed is used with a PRNG to determine where the salt is inserted
    within the value being hashed, adding an additional layer of randomization.
    
    Returns:
        bytes: 32-byte random position seed
    """
    return secrets.token_bytes(32)


def store_salt(salt_data: bytes, position_seed: bytes, output_path: str) -> None:
    """
    Store salt with encryption in binary format.
    
    Binary format:
        [salt_length: 2 bytes (uint16 big-endian)]
        [position_seed: 32 bytes]
        [encrypted_salt: variable length]
    
    Args:
        salt_data: The 32-byte cryptographic salt
        position_seed: The 32-byte position randomization seed
        output_path: Path where salt file will be saved
        
    Raises:
        SystemExit: If encryption fails or file write fails
    """
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(salt_data)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'wb') as file:
            # Write salt length (2 bytes, uint16 big-endian)
            file.write(struct.pack('!H', len(salt_data)))
            # Write position seed (32 bytes)
            file.write(position_seed)
            # Write encrypted salt (variable length)
            file.write(encrypted)
            
    except Exception as e:
        print(f"Error: Failed to save salt file: {output_path}", file=sys.stderr)
        print(f"  {str(e)}", file=sys.stderr)
        sys.exit(8)


def load_salt(salt_path: str) -> Tuple[bytes, bytes]:
    """
    Load and decrypt salt from file.
    
    Reads the binary salt file format and decrypts the salt using
    TF_ANALYZER_SALT_KEY environment variable.
    
    Args:
        salt_path: Path to the encrypted salt file
        
    Returns:
        Tuple of (salt_data, position_seed)
        
    Raises:
        SystemExit: If file not found (exit code 5) or decryption fails (exit code 6)
    """
    salt_file = Path(salt_path)
    
    # Check if file exists
    if not salt_file.exists():
        print(f"Error: Salt file not found: {salt_path}", file=sys.stderr)
        sys.exit(5)
    
    try:
        with open(salt_file, 'rb') as file:
            # Read salt length (2 bytes)
            salt_length_bytes = file.read(2)
            if len(salt_length_bytes) != 2:
                raise ValueError("Invalid salt file: missing salt length header")
            salt_length = struct.unpack('!H', salt_length_bytes)[0]
            
            # Read position seed (32 bytes)
            position_seed = file.read(32)
            if len(position_seed) != 32:
                raise ValueError("Invalid salt file: missing or incomplete position seed")
            
            # Read encrypted salt (rest of file)
            encrypted_data = file.read()
            if not encrypted_data:
                raise ValueError("Invalid salt file: missing encrypted salt data")
        
        # Decrypt salt
        key = get_encryption_key()
        f = Fernet(key)
        try:
            salt_data = f.decrypt(encrypted_data)
        except Exception as decrypt_error:
            print(f"Error: Failed to decrypt salt file: {salt_path}", file=sys.stderr)
            print(f"  Ensure TF_ANALYZER_SALT_KEY environment variable is set correctly", file=sys.stderr)
            print(f"  Decryption error: {str(decrypt_error)}", file=sys.stderr)
            sys.exit(6)
        
        return salt_data, position_seed
        
    except Exception as e:
        print(f"Error: Failed to read salt file: {salt_path}", file=sys.stderr)
        print(f"  {str(e)}", file=sys.stderr)
        sys.exit(6)
