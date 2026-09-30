import os

import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.backends import fail
from keyring.errors import PasswordDeleteError

from sparksdb import pool_manager


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path / "sparkdb"


class MemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self):
        super().__init__()
        self.passwords = {}

    def get_password(self, service, username):
        return self.passwords.get((service, username))

    def set_password(self, service, username, password):
        self.passwords[(service, username)] = password

    def delete_password(self, service, username):
        if (service, username) not in self.passwords:
            raise PasswordDeleteError(username)
        del self.passwords[(service, username)]


def _use_keyring(backend):
    previous = keyring.get_keyring()
    keyring.set_keyring(backend)
    return previous


@pytest.fixture
def memory_keyring():
    backend = MemoryKeyring()
    previous = _use_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


@pytest.fixture
def failing_keyring():
    previous = _use_keyring(fail.Keyring())
    yield
    keyring.set_keyring(previous)


@pytest.fixture
def pg_dsn():
    dsn = os.environ.get("SPARKSDB_TEST_DSN")
    if not dsn:
        pytest.skip("defina SPARKSDB_TEST_DSN para rodar os testes com Postgres")
    return dsn


@pytest.fixture
def pg_pool(pg_dsn):
    pool = pool_manager.open_pool(pg_dsn)
    yield pool
    pool.close()


@pytest.fixture
def pg_schema(pg_pool):
    def reset():
        with pg_pool.connection() as conn:
            conn.execute("DROP SCHEMA IF EXISTS sparksdb_test CASCADE")
    reset()
    with pg_pool.connection() as conn:
        conn.execute("CREATE SCHEMA sparksdb_test")
    yield "sparksdb_test"
    reset()
