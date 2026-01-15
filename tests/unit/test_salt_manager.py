"""Unit tests for salt_manager.py module."""

import pytest
import os
import tempfile
import base64
from cryptography.fernet import Fernet, InvalidToken
from src.security.salt_manager import generate_salt, generate_position_seed, store_salt, load_salt, get_encryption_key


class TestGenerateSalt:
    """Unit tests for generate_salt() function."""

    def test_salt_length(self):
        """Test that salt is 32 bytes."""
        salt = generate_salt()
        assert len(salt) == 32

    def test_salt_is_bytes(self):
        """Test that salt is bytes type."""
        salt = generate_salt()
        assert isinstance(salt, bytes)

    def test_salt_is_random(self):
        """Test that repeated calls produce different salts."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        assert salt1 != salt2

    def test_salt_entropy(self):
        """Test that salt has sufficient entropy (not all zeros or same byte)."""
        salt = generate_salt()
        unique_bytes = set(salt)
        # With 32 random bytes, we should have multiple unique values
        assert len(unique_bytes) > 10


class TestGeneratePositionSeed:
    """Unit tests for generate_position_seed() function."""

    def test_position_seed_length(self):
        """Test that position seed is 32 bytes."""
        seed = generate_position_seed()
        assert len(seed) == 32

    def test_position_seed_is_bytes(self):
        """Test that position seed is bytes type."""
        seed = generate_position_seed()
        assert isinstance(seed, bytes)

    def test_position_seed_is_random(self):
        """Test that repeated calls produce different seeds."""
        seed1 = generate_position_seed()
        seed2 = generate_position_seed()
        assert seed1 != seed2

    def test_position_seed_entropy(self):
        """Test that position seed has sufficient entropy."""
        seed = generate_position_seed()
        unique_bytes = set(seed)
        assert len(unique_bytes) > 10


class TestGetEncryptionKey:
    """Unit tests for get_encryption_key() function."""

    def test_get_key_from_environment(self, monkeypatch):
        """Test retrieving encryption key from environment variable."""
        test_key = Fernet.generate_key()
        monkeypatch.setenv("TF_ANALYZER_SALT_KEY", test_key.decode('utf-8'))
        
        key = get_encryption_key()
        
        assert key == test_key

    def test_get_key_generates_new_if_not_set(self, monkeypatch):
        """Test that a new key is generated if env var not set."""
        monkeypatch.delenv("TF_ANALYZER_SALT_KEY", raising=False)
        
        key = get_encryption_key()
        
        assert isinstance(key, bytes)
        assert len(key) == 44  # Fernet key is 44 bytes when base64 encoded

    def test_key_is_valid_fernet_key(self, monkeypatch):
        """Test that generated key is valid for Fernet."""
        monkeypatch.delenv("TF_ANALYZER_SALT_KEY", raising=False)
        
        key = get_encryption_key()
        fernet = Fernet(key)  # Should not raise exception
        
        # Test encryption/decryption works
        test_data = b"test"
        encrypted = fernet.encrypt(test_data)
        decrypted = fernet.decrypt(encrypted)
        assert decrypted == test_data

    def test_same_key_returned_when_env_var_set(self, monkeypatch):
        """Test that same key is returned when reading from env."""
        test_key = Fernet.generate_key()
        monkeypatch.setenv("TF_ANALYZER_SALT_KEY", test_key.decode('utf-8'))
        
        key1 = get_encryption_key()
        key2 = get_encryption_key()
        
        assert key1 == key2 == test_key


class TestStoreAndLoadSalt:
    """Unit tests for store_salt() and load_salt() functions."""

    def test_store_and_load_salt(self):
        """Test storing and loading a salt file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.salt') as f:
            salt_file = f.name
        
        try:
            salt = generate_salt()
            position_seed = generate_position_seed()
            
            # Store salt (correct order: salt_data, position_seed, output_path)
            store_salt(salt, position_seed, salt_file)
            
            # Verify file exists
            assert os.path.exists(salt_file)
            
            # Load salt
            loaded_salt, loaded_seed = load_salt(salt_file)
            
            # Verify loaded data matches original
            assert loaded_salt == salt
            assert loaded_seed == position_seed
        finally:
            if os.path.exists(salt_file):
                os.unlink(salt_file)

    def test_store_creates_file(self):
        """Test that store_salt creates the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            salt_file = os.path.join(tmpdir, 'test.salt')
            salt = generate_salt()
            position_seed = generate_position_seed()
            
            assert not os.path.exists(salt_file)
            
            store_salt(salt, position_seed, salt_file)
            
            assert os.path.exists(salt_file)

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading non-existent file raises SystemExit with code 5."""
        with pytest.raises(SystemExit) as exc_info:
            load_salt('/nonexistent/path/file.salt')
        assert exc_info.value.code == 5

    def test_load_corrupted_file_raises_error(self):
        """Test that loading corrupted file raises SystemExit with code 6."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.salt') as f:
            salt_file = f.name
            f.write(b'corrupted_data_not_valid_format')
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                load_salt(salt_file)
            assert exc_info.value.code == 6
        finally:
            os.unlink(salt_file)

    def test_salt_file_is_encrypted(self):
        """Test that salt file content is encrypted (not plaintext)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.salt') as f:
            salt_file = f.name
        
        try:
            salt = b'test_salt_1234567890123456789012'
            position_seed = generate_position_seed()
            
            store_salt(salt, position_seed, salt_file)
            
            # Read raw file content
            with open(salt_file, 'rb') as f:
                raw_content = f.read()
            
            # Salt should not appear in plaintext
            assert salt not in raw_content
            
            # Content should contain encrypted data (starts with 'gAAAAA' in base64)
            # Skip the first 34 bytes (salt_length + position_seed)
            encrypted_part = raw_content[34:]
            assert len(encrypted_part) > 0
        finally:
            os.unlink(salt_file)

    def test_store_overwrites_existing_file(self):
        """Test that storing to existing file overwrites it."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.salt') as f:
            salt_file = f.name
        
        try:
            salt1 = generate_salt()
            salt2 = generate_salt()
            position_seed = generate_position_seed()
            
            # Store first salt
            store_salt(salt1, position_seed, salt_file)
            loaded1, _ = load_salt(salt_file)
            assert loaded1 == salt1
            
            # Store second salt (overwrite)
            store_salt(salt2, position_seed, salt_file)
            loaded2, _ = load_salt(salt_file)
            assert loaded2 == salt2
            assert loaded2 != loaded1
        finally:
            os.unlink(salt_file)

    def test_load_with_environment_key(self, monkeypatch):
        """Test loading salt file with environment variable encryption key."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.salt') as f:
            salt_file = f.name
        
        try:
            # Set encryption key in environment
            test_key = Fernet.generate_key()
            monkeypatch.setenv("TF_ANALYZER_SALT_KEY", test_key.decode('utf-8'))
            
            salt = generate_salt()
            position_seed = generate_position_seed()
            
            # Store with env key
            store_salt(salt, position_seed, salt_file)
            
            # Load with same env key
            loaded_salt, loaded_seed = load_salt(salt_file)
            
            assert loaded_salt == salt
            assert loaded_seed == position_seed
        finally:
            if os.path.exists(salt_file):
                os.unlink(salt_file)

    def test_load_fails_with_different_key(self, monkeypatch):
        """Test that loading fails when encryption key is different."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.salt') as f:
            salt_file = f.name
        
        try:
            # Store with first key
            key1 = Fernet.generate_key()
            monkeypatch.setenv("TF_ANALYZER_SALT_KEY", key1.decode('utf-8'))
            
            salt = generate_salt()
            position_seed = generate_position_seed()
            store_salt(salt, position_seed, salt_file)
            
            # Try to load with different key
            key2 = Fernet.generate_key()
            monkeypatch.setenv("TF_ANALYZER_SALT_KEY", key2.decode('utf-8'))
            
            with pytest.raises(SystemExit) as exc_info:
                load_salt(salt_file)
            assert exc_info.value.code == 6
        finally:
            if os.path.exists(salt_file):
                os.unlink(salt_file)

    def test_binary_format_structure(self):
        """Test that salt file has correct binary structure."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.salt') as f:
            salt_file = f.name
        
        try:
            salt = generate_salt()
            position_seed = generate_position_seed()
            
            store_salt(salt, position_seed, salt_file)
            
            # Read raw binary data
            with open(salt_file, 'rb') as f:
                data = f.read()
            
            # Check format: [salt_length(2) + position_seed(32) + encrypted_salt(variable)]
            assert len(data) > 34  # At least header + some encrypted data
            
            # Extract salt length (first 2 bytes)
            import struct
            salt_length = struct.unpack('!H', data[:2])[0]
            assert salt_length == 32  # Our salt is always 32 bytes
            
            # Extract position seed (next 32 bytes)
            extracted_seed = data[2:34]
            assert extracted_seed == position_seed
            
            # Remaining bytes should be encrypted salt
            encrypted_salt = data[34:]
            assert len(encrypted_salt) > 0
        finally:
            os.unlink(salt_file)
