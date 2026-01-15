"""Unit tests for sensitive_obfuscator.py module."""

import pytest
import hashlib
from src.security.sensitive_obfuscator import obfuscate_value, get_salt_position, traverse_and_obfuscate


class TestObfuscateValue:
    """Unit tests for obfuscate_value() function."""

    def test_obfuscate_string_value(self):
        """Test obfuscation of a string value."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8  # 32 bytes
        value = "SecretPassword123"
        
        result = obfuscate_value(value, salt, position_seed)
        
        assert result.startswith("obf_")
        assert len(result) == 68  # "obf_" + 64 hex chars
        assert all(c in '0123456789abcdef' for c in result[4:])

    def test_obfuscate_integer_value(self):
        """Test obfuscation of an integer value."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        value = 12345
        
        result = obfuscate_value(value, salt, position_seed)
        
        assert result.startswith("obf_")
        assert len(result) == 68

    def test_obfuscate_boolean_value(self):
        """Test obfuscation of a boolean value."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        value = True
        
        result = obfuscate_value(value, salt, position_seed)
        
        assert result.startswith("obf_")
        assert len(result) == 68

    def test_obfuscate_null_value(self):
        """Test obfuscation of a null value."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        value = None
        
        result = obfuscate_value(value, salt, position_seed)
        
        assert result.startswith("obf_")
        assert len(result) == 68

    def test_deterministic_output(self):
        """Test that same input produces same output."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        value = "SecretPassword123"
        
        result1 = obfuscate_value(value, salt, position_seed)
        result2 = obfuscate_value(value, salt, position_seed)
        
        assert result1 == result2

    def test_different_values_produce_different_hashes(self):
        """Test that different values produce different hashes."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        
        result1 = obfuscate_value("password1", salt, position_seed)
        result2 = obfuscate_value("password2", salt, position_seed)
        
        assert result1 != result2

    def test_different_salts_produce_different_hashes(self):
        """Test that different salts produce different hashes for same value."""
        salt1 = b'test_salt_1111111111111111111111'
        salt2 = b'test_salt_2222222222222222222222'
        position_seed = b'seed' * 8
        value = "SecretPassword123"
        
        result1 = obfuscate_value(value, salt1, position_seed)
        result2 = obfuscate_value(value, salt2, position_seed)
        
        assert result1 != result2

    def test_salt_position_affects_hash(self):
        """Test that salt position affects the final hash."""
        salt = b'test_salt_1234567890123456789012'
        position_seed1 = b'seed1' + b'0' * 27
        position_seed2 = b'seed2' + b'0' * 27
        value = "SecretPassword123"
        
        result1 = obfuscate_value(value, salt, position_seed1)
        result2 = obfuscate_value(value, salt, position_seed2)
        
        # Different position seeds should produce different hashes
        assert result1 != result2


class TestGetSaltPosition:
    """Unit tests for get_salt_position() function."""

    def test_position_within_bounds_for_short_value(self):
        """Test that position is valid for short values."""
        position_seed = b'test_seed_1234567890123456789012'
        value_bytes = b"short"
        
        position = get_salt_position(value_bytes, position_seed, len(value_bytes))
        
        assert 0 <= position <= len(value_bytes)

    def test_position_within_bounds_for_long_value(self):
        """Test that position is valid for long values."""
        position_seed = b'test_seed_1234567890123456789012'
        value_bytes = b"a" * 1000
        
        position = get_salt_position(value_bytes, position_seed, len(value_bytes))
        
        assert 0 <= position <= len(value_bytes)

    def test_deterministic_position(self):
        """Test that same seed produces same position."""
        position_seed = b'test_seed_1234567890123456789012'
        value_bytes = b"test_value"
        
        pos1 = get_salt_position(value_bytes, position_seed, len(value_bytes))
        pos2 = get_salt_position(value_bytes, position_seed, len(value_bytes))
        
        assert pos1 == pos2

    def test_different_seeds_produce_different_positions(self):
        """Test that different seeds can produce different positions."""
        seed1 = b'test_seed_1111111111111111111111'
        seed2 = b'test_seed_2222222222222222222222'
        value_bytes = b"test_value_long_enough_to_vary"
        
        pos1 = get_salt_position(value_bytes, seed1, len(value_bytes))
        pos2 = get_salt_position(value_bytes, seed2, len(value_bytes))
        
        # With high probability, different seeds should give different positions
        # (Not guaranteed, but very likely with 32-character value)
        # This test might occasionally fail due to randomness, but should pass >99% of the time
        assert pos1 != pos2 or len(value_bytes) < 2  # Allow equality only for very short values


class TestTraverseAndObfuscate:
    """Unit tests for traverse_and_obfuscate() function."""

    def test_obfuscate_simple_structure(self):
        """Test obfuscation of simple data structure."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        
        data = {
            "password": "secret123",
            "username": "admin"
        }
        sensitive = {
            "password": True,
            "username": False
        }
        
        result = traverse_and_obfuscate(data, sensitive, salt, position_seed)
        
        assert result["password"].startswith("obf_")
        assert result["username"] == "admin"

    def test_obfuscate_nested_structure(self):
        """Test obfuscation of nested data structure."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        
        data = {
            "database": {
                "host": "db.example.com",
                "password": "secret123"
            }
        }
        sensitive = {
            "database": {
                "host": False,
                "password": True
            }
        }
        
        result = traverse_and_obfuscate(data, sensitive, salt, position_seed)
        
        assert result["database"]["host"] == "db.example.com"
        assert result["database"]["password"].startswith("obf_")

    def test_obfuscate_list_structure(self):
        """Test obfuscation of list structure."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        
        data = ["public", "secret"]
        sensitive = [False, True]
        
        result = traverse_and_obfuscate(data, sensitive, salt, position_seed)
        
        assert result[0] == "public"
        assert result[1].startswith("obf_")

    def test_no_sensitive_marker(self):
        """Test that data without sensitive marker is returned unchanged."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        
        data = {
            "password": "secret123",
            "username": "admin"
        }
        sensitive = {}
        
        result = traverse_and_obfuscate(data, sensitive, salt, position_seed)
        
        assert result["password"] == "secret123"
        assert result["username"] == "admin"

    def test_preserve_non_sensitive_nested_data(self):
        """Test that non-sensitive nested data is preserved."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        
        data = {
            "config": {
                "public_key": "pk_123",
                "private_key": "sk_456"
            },
            "metadata": {
                "version": "1.0"
            }
        }
        sensitive = {
            "config": {
                "public_key": False,
                "private_key": True
            }
        }
        
        result = traverse_and_obfuscate(data, sensitive, salt, position_seed)
        
        assert result["config"]["public_key"] == "pk_123"
        assert result["config"]["private_key"].startswith("obf_")
        assert result["metadata"] == {"version": "1.0"}

    def test_deeply_nested_structure(self):
        """Test obfuscation of deeply nested structure."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "secret": "deep_secret"
                        }
                    }
                }
            }
        }
        sensitive = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "secret": True
                        }
                    }
                }
            }
        }
        
        result = traverse_and_obfuscate(data, sensitive, salt, position_seed)
        
        assert result["level1"]["level2"]["level3"]["level4"]["secret"].startswith("obf_")

    def test_mixed_types_in_structure(self):
        """Test obfuscation with mixed value types."""
        salt = b'test_salt_1234567890123456789012'
        position_seed = b'seed' * 8
        
        data = {
            "string_value": "secret",
            "int_value": 12345,
            "bool_value": True,
            "null_value": None
        }
        sensitive = {
            "string_value": True,
            "int_value": True,
            "bool_value": True,
            "null_value": True
        }
        
        result = traverse_and_obfuscate(data, sensitive, salt, position_seed)
        
        assert all(v.startswith("obf_") for v in result.values())
