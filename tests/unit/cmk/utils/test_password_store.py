#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from pathlib import Path
from typing import Iterator

import pytest

import cmk.utils.paths
from cmk.utils import password_store
from cmk.utils.config_path import LATEST_CONFIG
from cmk.utils.crypto.secrets import PasswordStoreSecret
from cmk.utils.exceptions import MKGeneralException
from cmk.utils.password_store import PasswordId

PW_STORE = "pw_from_store"
PW_EXPL = "pw_explicit"
PW_STORE_KEY = "from_store"


@pytest.fixture(name="fixed_secret")
def fixture_fixed_secret(tmp_path: Path) -> Iterator[None]:
    """Write a fixed value to a tmp file and use that file for the password store secret

    we need the old value since other tests rely on the general path mocking"""
    old_path = PasswordStoreSecret.path
    secret = b"password-secret"
    secret_path = tmp_path / "password_store_fixed.secret"
    secret_path.write_bytes(secret)
    PasswordStoreSecret.path = secret_path
    yield
    PasswordStoreSecret.path = old_path


def test_save() -> None:
    assert password_store.load() == {}
    password_store.save({"ding": "blablu"})
    assert password_store.load()["ding"] == "blablu"


def test_save_for_helpers_no_store() -> None:
    assert not password_store.password_store_path().exists()

    assert password_store.load_for_helpers() == {}
    password_store.save_for_helpers(LATEST_CONFIG)

    assert not password_store.password_store_path().exists()
    assert not password_store._helper_password_store_path(LATEST_CONFIG).exists()
    assert password_store.load_for_helpers() == {}


def test_save_for_helpers() -> None:
    assert not password_store.password_store_path().exists()
    password_store.save({"ding": "blablu"})
    assert password_store.password_store_path().exists()
    assert password_store.load_for_helpers() == {}

    password_store.save_for_helpers(LATEST_CONFIG)
    assert password_store.load_for_helpers() == {"ding": "blablu"}


def load_patch() -> dict[str, str]:
    return {PW_STORE_KEY: PW_STORE}


@pytest.mark.parametrize(
    "password_id, password_actual",
    [
        (("password", PW_EXPL), PW_EXPL),
        (("store", PW_STORE_KEY), PW_STORE),
        (PW_STORE_KEY, PW_STORE),
    ],
)
def test_extract(
    monkeypatch: pytest.MonkeyPatch,
    password_id: PasswordId,
    password_actual: str,
) -> None:
    monkeypatch.setattr(password_store, "load", load_patch)
    assert password_store.extract(password_id) == password_actual


def test_extract_from_unknown_valuespec() -> None:
    password_id = ("unknown", "unknown_pw")
    with pytest.raises(MKGeneralException) as excinfo:
        # We test for an invalid structure here
        password_store.extract(password_id)  # type: ignore[arg-type]
    assert "Unknown password type." in str(excinfo.value)


def test_obfuscation() -> None:
    obfuscated = password_store._obfuscate(secret := "$ecret")
    assert (
        int.from_bytes(
            obfuscated[: password_store.PasswordStore.VERSION_BYTE_LENGTH],
            byteorder="big",
        )
        == password_store.PasswordStore.VERSION
    )
    assert password_store._deobfuscate(obfuscated) == secret


def test_save_obfuscated() -> None:
    password_store.save(data := {"ding": "blablu"})
    assert password_store.load() == data


def test_obfuscate_with_own_secret() -> None:
    obfuscated = password_store._obfuscate(secret := "$ecret")
    assert password_store._deobfuscate(obfuscated) == secret

    # The user may want to write some arbritary secret to the file.
    cmk.utils.paths.password_store_secret_file.write_bytes(b"this_will_be_pretty_secure_now.not.")

    # Old should not be decryptable anymore
    with pytest.raises(ValueError, match="MAC check failed"):
        assert password_store._deobfuscate(obfuscated)

    # Test encryption and decryption with new key
    assert password_store._deobfuscate(password_store._obfuscate(secret)) == secret


def test_encrypt_decrypt_identity() -> None:
    data = "some random data to be encrypted"
    assert password_store.PasswordStore.decrypt(password_store.PasswordStore.encrypt(data)) == data


@pytest.mark.usefixtures("fixed_secret")
def test_pw_store_characterization() -> None:
    """This is a characterization (aka "golden master") test to ensure that the password store can
    still decrypt passwords it encrypted before.

    This can only work if the local secret is fixed of course, but a change in the container format,
    the key generation, or algorithms used would be detected.
    """
    # generated by PasswordStore._obfuscate as of commit 79900beda42310dfea9f5bd704041f4e10936ba8
    encrypted = (
        b"\x00\x00;\x1c\xed\xb9%&b\x14\x83\xf9\xba\x14\x0f\xbeU\xf4\x99\x16\xaew\xa1\x1a*\xc9;M\xb0"
        b"u\x80aq\xa6*\x8a\xed\xd3\xd1\xed\xd6~U\x83\x85\xa9\x8e\xfe\xbe<L\x0c\xa3d\xe5O\xf6\xad/"
        b"\xa7\xefH\xa0\xe8\x8e\xd9\x89(>\x96\x04\xe0}\xa8\x93\x01e\x8f\x03p\xd3[\xba\x1a\x8a\xbft"
        b"\xbc\x97\x19u"
    )

    assert password_store._deobfuscate(encrypted) == "Time is an illusion. Lunchtime doubly so."
