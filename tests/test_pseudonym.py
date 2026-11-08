"""INTENT-002 finding B: logged caller ids are keyed pseudonyms, not dictionary-reversible."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from iat.api.app import create_app
from iat.core.config import Settings
from iat.security.pseudonym import PSEUDONYM_HEX_CHARS, SubjectPseudonymizer, derive_key
from tests.conftest import AS_OF, INVOKE, TEST_SECRET, TokenFactory

LIKELY_SUBJECTS = ["alice", "bob", "admin", "root", "mark", "alice@example.com", "svc-batch"]


def _unkeyed_guesses(subject: str) -> set[str]:
    """What an attacker with only the logs can compute (INTENT-001 scheme and variants)."""
    out = set()
    for algo in ("sha256", "sha1", "md5", "sha512"):
        full = hashlib.new(algo, subject.encode()).hexdigest()
        out |= {full, full[:16], full[:32]}
    return out


def test_pseudonym_is_not_the_intent_001_hash() -> None:
    pseudonym = SubjectPseudonymizer(b"k" * 32)("alice")
    assert pseudonym != hashlib.sha256(b"alice").hexdigest()[:16]
    assert len(pseudonym) == PSEUDONYM_HEX_CHARS


def test_dictionary_attack_without_key_finds_no_match() -> None:
    pseudonymize = SubjectPseudonymizer(derive_key(SecretStr(TEST_SECRET), None))
    logged = {pseudonymize(s) for s in LIKELY_SUBJECTS}
    attacker_table = set().union(*(_unkeyed_guesses(s) for s in LIKELY_SUBJECTS))
    assert logged.isdisjoint(attacker_table)
    # Guessing with a wrong key does not work either.
    wrong = SubjectPseudonymizer(b"w" * 32)
    assert logged.isdisjoint({wrong(s) for s in LIKELY_SUBJECTS})


def test_pseudonym_supports_correlation() -> None:
    pseudonymize = SubjectPseudonymizer(b"k" * 32)
    assert pseudonymize("alice") == pseudonymize("alice")
    assert pseudonymize("alice") != pseudonymize("bob")


def test_different_keys_produce_unlinkable_pseudonyms() -> None:
    assert SubjectPseudonymizer(b"a" * 32)("alice") != SubjectPseudonymizer(b"b" * 32)("alice")


def test_derived_key_is_domain_separated_from_jwt_secret() -> None:
    derived = derive_key(SecretStr(TEST_SECRET), None)
    assert derived != TEST_SECRET.encode()
    expected = hmac.new(TEST_SECRET.encode(), b"iat/subject-pseudonym/v1", hashlib.sha256).digest()
    assert derived == expected


def test_explicit_key_overrides_derivation() -> None:
    explicit = SecretStr("p" * 40)
    assert derive_key(SecretStr(TEST_SECRET), explicit) == b"p" * 40


def test_short_pseudonym_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="IAT_SUBJECT_PSEUDONYM_KEY"):
        Settings(
            jwt_secret=SecretStr(TEST_SECRET),
            subject_pseudonym_key=SecretStr("short"),
            _env_file=None,  # type: ignore[call-arg]
        )


def test_pseudonymizer_never_renders_its_key() -> None:
    pseudonymize = SubjectPseudonymizer(b"secret-key-material-" * 2)
    assert "secret-key-material" not in repr(pseudonymize)


def test_logs_and_response_carry_keyed_pseudonym_only(
    settings: Settings, make_token: TokenFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    with TestClient(create_app(settings)) as client:
        body = client.post(
            INVOKE,
            json={"message": "Can Supplier Acme be approved?"},
            headers={"Authorization": f"Bearer {make_token('alice')}"},
        ).json()
    out = capsys.readouterr().out
    expected = SubjectPseudonymizer(derive_key(settings.jwt_secret, None))("alice")
    assert body["execution"]["subject_hash"] == expected
    assert expected in out
    for guess in _unkeyed_guesses("alice"):
        assert guess not in out
    assert "alice" not in out
    lines = [json.loads(line) for line in out.splitlines() if line.startswith("{")]
    assert all(TEST_SECRET not in json.dumps(line) for line in lines)
    assert AS_OF.isoformat() == body["output"]["as_of"]
