"""At-rest encryption for the mobile session file on Android.

The AES key lives in the Android Keystore and never leaves it.  On desktop
(where the Keystore is unavailable) callers fall back to the previous
permission-protected JSON file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

MAGIC = "ECS1"
_ALIAS = "electrocalc_session_v1"


def _is_android():
    try:
        from kivy.utils import platform

        return platform == "android"
    except Exception:
        return False


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    temporary.replace(path)


def _keystore_key():
    from jnius import autoclass

    key_store = autoclass("java.security.KeyStore")
    key_generator = autoclass("javax.crypto.KeyGenerator")
    key_properties = autoclass("android.security.keystore.KeyProperties")
    spec_builder = autoclass("android.security.keystore.KeyGenParameterSpec$Builder")

    store = key_store.getInstance("AndroidKeyStore")
    store.load(None)
    if not store.containsAlias(_ALIAS):
        builder = spec_builder(
            _ALIAS,
            key_properties.PURPOSE_ENCRYPT | key_properties.PURPOSE_DECRYPT,
        )
        builder.setKeySize(256)
        try:
            builder.setBlockModes([key_properties.BLOCK_MODE_GCM])
            builder.setEncryptionPaddings(
                [key_properties.ENCRYPTION_PADDING_NONE]
            )
        except Exception:
            builder.setBlockModes(key_properties.BLOCK_MODE_GCM)
            builder.setEncryptionPaddings(
                key_properties.ENCRYPTION_PADDING_NONE
            )
        generator = key_generator.getInstance(
            key_properties.KEY_ALGORITHM_AES, "AndroidKeyStore"
        )
        generator.init(builder.build())
        generator.generateKey()
    return store.getKey(_ALIAS, None)


def write_encrypted(path: Path, payload: bytes) -> bool:
    if not _is_android():
        return False
    try:
        from jnius import autoclass

        cipher_class = autoclass("javax.crypto.Cipher")
        base64 = autoclass("android.util.Base64")
        key = _keystore_key()
        cipher = cipher_class.getInstance("AES/GCM/NoPadding")
        cipher.init(cipher_class.ENCRYPT_MODE, key)
        iv = base64.encodeToString(cipher.getIV(), base64.NO_WRAP)
        encrypted = base64.encodeToString(
            cipher.doFinal(payload), base64.NO_WRAP
        )
        document = json.dumps(
            {"magic": MAGIC, "iv": iv, "data": encrypted},
            separators=(",", ":"),
        ).encode("utf-8")
        _write_atomic(path, document)
        return True
    except Exception:
        return False


def read_encrypted(path: Path) -> bytes | None:
    if not _is_android():
        return None
    try:
        from jnius import autoclass

        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("magic") != MAGIC:
            return None
        cipher_class = autoclass("javax.crypto.Cipher")
        base64 = autoclass("android.util.Base64")
        gcm_spec = autoclass("javax.crypto.spec.GCMParameterSpec")
        key = _keystore_key()
        cipher = cipher_class.getInstance("AES/GCM/NoPadding")
        iv = base64.decode(document["iv"], base64.NO_WRAP)
        encrypted = base64.decode(document["data"], base64.NO_WRAP)
        cipher.init(
            cipher_class.DECRYPT_MODE, key, gcm_spec(128, iv)
        )
        result = cipher.doFinal(encrypted)
        try:
            return bytes(result)
        except TypeError:
            return bytes(bytearray(result))
    except Exception:
        return None
