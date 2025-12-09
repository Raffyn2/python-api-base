"""Unit tests for infrastructure/security/field_encryption.py.

Tests field-level encryption and decryption.

**Task 21.1: Create tests for field_encryption.py**
**Requirements: 4.4**
"""

import pytest

from infrastructure.security.field_encryption import (
    EncryptedValue,
    EncryptionAlgorithm,
    FieldEncryptor,
    InMemoryKeyProvider,
)


class TestEncryptedValue:
    """Tests for EncryptedValue dataclass."""

    def test_to_string(self) -> None:
        """Test serialization to string."""
        value = EncryptedValue(
            ciphertext=b"encrypted_data",
            key_id="key-123",
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            nonce=b"nonce_value_",
            tag=b"tag_value_123456",
        )

        result = value.to_string()

        assert "key-123" in result
        assert "aes-256-gcm" in result

    def test_from_string(self) -> None:
        """Test deserialization from string."""
        value = EncryptedValue(
            ciphertext=b"encrypted_data",
            key_id="key-123",
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            nonce=b"nonce_value_",
            tag=b"tag_value_123456",
        )
        serialized = value.to_string()

        restored = EncryptedValue.from_string(serialized)

        assert restored.key_id == "key-123"
        assert restored.algorithm == EncryptionAlgorithm.AES_256_GCM

    def test_from_string_invalid_format(self) -> None:
        """Test from_string with invalid format raises."""
        from core.errors.shared.exceptions import DecryptionError

        with pytest.raises(DecryptionError, match="Invalid encrypted value"):
            EncryptedValue.from_string("invalid:format")


class TestInMemoryKeyProvider:
    """Tests for InMemoryKeyProvider."""

    @pytest.mark.asyncio
    async def test_get_active_key(self) -> None:
        """Test getting active key."""
        provider = InMemoryKeyProvider()

        key_id, key = await provider.get_active_key()

        assert key_id is not None
        assert len(key) == 32  # 256 bits

    @pytest.mark.asyncio
    async def test_get_key(self) -> None:
        """Test getting key by ID."""
        provider = InMemoryKeyProvider()
        key_id, _ = await provider.get_active_key()

        key = await provider.get_key(key_id)

        assert key is not None
        assert len(key) == 32

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self) -> None:
        """Test getting nonexistent key returns None."""
        provider = InMemoryKeyProvider()

        key = await provider.get_key("nonexistent")

        assert key is None

    @pytest.mark.asyncio
    async def test_rotate_key(self) -> None:
        """Test key rotation."""
        provider = InMemoryKeyProvider()
        old_key_id, _ = await provider.get_active_key()

        new_key_id, _ = await provider.rotate_key()

        assert new_key_id != old_key_id


class TestFieldEncryptor:
    """Tests for FieldEncryptor."""

    @pytest.mark.asyncio
    async def test_encrypt_string(self) -> None:
        """Test encrypting a string."""
        provider = InMemoryKeyProvider()
        encryptor = FieldEncryptor(provider)

        result = await encryptor.encrypt("secret data")

        assert result.ciphertext is not None
        assert result.algorithm == EncryptionAlgorithm.AES_256_GCM
        assert result.nonce is not None
        assert result.tag is not None

    @pytest.mark.asyncio
    async def test_encrypt_bytes(self) -> None:
        """Test encrypting bytes."""
        provider = InMemoryKeyProvider()
        encryptor = FieldEncryptor(provider)

        result = await encryptor.encrypt(b"secret bytes")

        assert result.ciphertext is not None

    @pytest.mark.asyncio
    async def test_decrypt(self) -> None:
        """Test decrypting encrypted value."""
        provider = InMemoryKeyProvider()
        encryptor = FieldEncryptor(provider)
        plaintext = "secret data"

        encrypted = await encryptor.encrypt(plaintext)
        decrypted = await encryptor.decrypt(encrypted)

        assert decrypted.decode("utf-8") == plaintext

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip(self) -> None:
        """Test encrypt/decrypt roundtrip."""
        provider = InMemoryKeyProvider()
        encryptor = FieldEncryptor(provider)
        original = "sensitive information"

        encrypted = await encryptor.encrypt(original)
        decrypted = await encryptor.decrypt(encrypted)

        assert decrypted.decode("utf-8") == original

    @pytest.mark.asyncio
    async def test_unsupported_algorithm_raises(self) -> None:
        """Test unsupported algorithm raises error."""
        from core.errors.shared.exceptions import EncryptionError

        provider = InMemoryKeyProvider()
        encryptor = FieldEncryptor(provider)

        with pytest.raises(EncryptionError, match="Unsupported algorithm"):
            await encryptor.encrypt("data", EncryptionAlgorithm.AES_256_CBC)

    @pytest.mark.asyncio
    async def test_rotate_encrypted_value(self) -> None:
        """Test re-encrypting with new key."""
        provider = InMemoryKeyProvider()
        encryptor = FieldEncryptor(provider)
        plaintext = "secret data"

        encrypted = await encryptor.encrypt(plaintext)
        old_key_id = encrypted.key_id

        await provider.rotate_key()
        rotated = await encryptor.rotate_encrypted_value(encrypted)

        assert rotated.key_id != old_key_id
        decrypted = await encryptor.decrypt(rotated)
        assert decrypted.decode("utf-8") == plaintext
