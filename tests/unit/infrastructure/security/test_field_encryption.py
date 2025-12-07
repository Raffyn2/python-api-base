"""Unit tests for field-level encryption.

Tests FieldEncryptor, EncryptedValue, and InMemoryKeyProvider.
"""

import pytest

from infrastructure.security.field_encryption import (
    KEY_SIZE,
    NONCE_SIZE,
    EncryptedValue,
    EncryptionAlgorithm,
    EncryptionKey,
    FieldEncryptor,
    InMemoryKeyProvider,
)


class TestEncryptionAlgorithm:
    """Tests for EncryptionAlgorithm enum."""

    def test_aes_256_gcm_value(self) -> None:
        """Test AES-256-GCM enum value."""
        assert EncryptionAlgorithm.AES_256_GCM.value == "aes-256-gcm"

    def test_aes_256_cbc_value(self) -> None:
        """Test AES-256-CBC enum value."""
        assert EncryptionAlgorithm.AES_256_CBC.value == "aes-256-cbc"

    def test_chacha20_poly1305_value(self) -> None:
        """Test ChaCha20-Poly1305 enum value."""
        assert EncryptionAlgorithm.CHACHA20_POLY1305.value == "chacha20-poly1305"


class TestEncryptionKey:
    """Tests for EncryptionKey dataclass."""

    def test_creation(self) -> None:
        """Test EncryptionKey creation."""
        from datetime import UTC, datetime

        key = EncryptionKey(
            key_id="key-1",
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            created_at=datetime.now(UTC),
        )

        assert key.key_id == "key-1"
        assert key.algorithm == EncryptionAlgorithm.AES_256_GCM
        assert key.is_active is True
        assert key.version == 1
        assert key.expires_at is None

    def test_with_expiration(self) -> None:
        """Test EncryptionKey with expiration."""
        from datetime import UTC, datetime, timedelta

        now = datetime.now(UTC)
        key = EncryptionKey(
            key_id="key-1",
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            created_at=now,
            expires_at=now + timedelta(days=30),
        )

        assert key.expires_at is not None



class TestEncryptedValue:
    """Tests for EncryptedValue dataclass."""

    def test_to_string(self) -> None:
        """Test serialization to string."""
        value = EncryptedValue(
            ciphertext=b"encrypted_data",
            key_id="key-1",
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            nonce=b"123456789012",
            tag=b"1234567890123456",
            version=2,
        )

        result = value.to_string()

        assert "key-1" in result
        assert "aes-256-gcm" in result
        assert "2" in result

    def test_from_string(self) -> None:
        """Test deserialization from string."""
        value = EncryptedValue(
            ciphertext=b"encrypted_data",
            key_id="key-1",
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            nonce=b"123456789012",
            tag=b"1234567890123456",
            version=2,
        )
        serialized = value.to_string()

        restored = EncryptedValue.from_string(serialized)

        assert restored.key_id == "key-1"
        assert restored.algorithm == EncryptionAlgorithm.AES_256_GCM
        assert restored.version == 2
        assert restored.ciphertext == b"encrypted_data"

    def test_from_string_invalid_format(self) -> None:
        """Test deserialization with invalid format."""
        from core.errors.shared.exceptions import DecryptionError

        with pytest.raises(DecryptionError, match="Invalid encrypted value format"):
            EncryptedValue.from_string("invalid:format")

    def test_roundtrip_without_tag(self) -> None:
        """Test serialization roundtrip without tag."""
        value = EncryptedValue(
            ciphertext=b"data",
            key_id="key-1",
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            nonce=b"123456789012",
            tag=None,
            version=2,
        )

        serialized = value.to_string()
        restored = EncryptedValue.from_string(serialized)

        assert restored.tag is None


class TestInMemoryKeyProvider:
    """Tests for InMemoryKeyProvider."""

    @pytest.fixture
    def provider(self) -> InMemoryKeyProvider:
        """Create provider instance."""
        return InMemoryKeyProvider()

    @pytest.mark.asyncio
    async def test_get_active_key(self, provider: InMemoryKeyProvider) -> None:
        """Test getting active key."""
        key_id, key = await provider.get_active_key()

        assert key_id is not None
        assert len(key) == KEY_SIZE

    @pytest.mark.asyncio
    async def test_get_key_by_id(self, provider: InMemoryKeyProvider) -> None:
        """Test getting key by ID."""
        key_id, _ = await provider.get_active_key()

        key = await provider.get_key(key_id)

        assert key is not None
        assert len(key) == KEY_SIZE

    @pytest.mark.asyncio
    async def test_get_key_not_found(self, provider: InMemoryKeyProvider) -> None:
        """Test getting non-existent key."""
        key = await provider.get_key("non-existent")

        assert key is None

    @pytest.mark.asyncio
    async def test_rotate_key(self, provider: InMemoryKeyProvider) -> None:
        """Test key rotation."""
        old_key_id, _ = await provider.get_active_key()

        new_key_id, new_key = await provider.rotate_key()

        assert new_key_id != old_key_id
        assert len(new_key) == KEY_SIZE

    @pytest.mark.asyncio
    async def test_list_keys(self, provider: InMemoryKeyProvider) -> None:
        """Test listing all keys."""
        await provider.rotate_key()
        await provider.rotate_key()

        keys = await provider.list_keys()

        assert len(keys) >= 2


class TestFieldEncryptor:
    """Tests for FieldEncryptor."""

    @pytest.fixture
    def provider(self) -> InMemoryKeyProvider:
        """Create key provider."""
        return InMemoryKeyProvider()

    @pytest.fixture
    def encryptor(self, provider: InMemoryKeyProvider) -> FieldEncryptor:
        """Create encryptor instance."""
        return FieldEncryptor(provider)

    @pytest.mark.asyncio
    async def test_encrypt_string(self, encryptor: FieldEncryptor) -> None:
        """Test encrypting string."""
        plaintext = "sensitive data"

        encrypted = await encryptor.encrypt(plaintext)

        assert encrypted.ciphertext != plaintext.encode()
        assert encrypted.algorithm == EncryptionAlgorithm.AES_256_GCM
        assert len(encrypted.nonce) == NONCE_SIZE
        assert encrypted.tag is not None

    @pytest.mark.asyncio
    async def test_encrypt_bytes(self, encryptor: FieldEncryptor) -> None:
        """Test encrypting bytes."""
        plaintext = b"binary data"

        encrypted = await encryptor.encrypt(plaintext)

        assert encrypted.ciphertext != plaintext

    @pytest.mark.asyncio
    async def test_decrypt(self, encryptor: FieldEncryptor) -> None:
        """Test decryption."""
        plaintext = "secret message"
        encrypted = await encryptor.encrypt(plaintext)

        decrypted = await encryptor.decrypt(encrypted)

        assert decrypted == plaintext.encode()

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip(self, encryptor: FieldEncryptor) -> None:
        """Test encryption/decryption roundtrip."""
        original = "The quick brown fox jumps over the lazy dog"

        encrypted = await encryptor.encrypt(original)
        decrypted = await encryptor.decrypt(encrypted)

        assert decrypted.decode() == original

    @pytest.mark.asyncio
    async def test_encrypt_unsupported_algorithm(
        self, encryptor: FieldEncryptor
    ) -> None:
        """Test encryption with unsupported algorithm."""
        from core.errors.shared.exceptions import EncryptionError

        with pytest.raises(EncryptionError, match="Unsupported algorithm"):
            await encryptor.encrypt("data", EncryptionAlgorithm.AES_256_CBC)

    @pytest.mark.asyncio
    async def test_decrypt_key_not_found(self, encryptor: FieldEncryptor) -> None:
        """Test decryption with missing key."""
        from core.errors.shared.exceptions import DecryptionError

        encrypted = EncryptedValue(
            ciphertext=b"data",
            key_id="non-existent-key",
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            nonce=b"123456789012",
            tag=b"1234567890123456",
        )

        with pytest.raises(DecryptionError, match="Key not found"):
            await encryptor.decrypt(encrypted)

    @pytest.mark.asyncio
    async def test_rotate_encrypted_value(self, encryptor: FieldEncryptor) -> None:
        """Test re-encrypting with new key."""
        plaintext = "data to rotate"
        encrypted = await encryptor.encrypt(plaintext)
        old_key_id = encrypted.key_id

        # Rotate key
        await encryptor._key_provider.rotate_key()

        # Re-encrypt
        rotated = await encryptor.rotate_encrypted_value(encrypted)

        assert rotated.key_id != old_key_id
        decrypted = await encryptor.decrypt(rotated)
        assert decrypted.decode() == plaintext

    def test_xor_encrypt_deprecated(self, encryptor: FieldEncryptor) -> None:
        """Test XOR encryption raises deprecation warning and error."""
        from core.errors.shared.exceptions import EncryptionError

        with pytest.warns(DeprecationWarning):
            with pytest.raises(EncryptionError, match="XOR encryption is deprecated"):
                encryptor._xor_encrypt(b"data", b"key", b"nonce")
