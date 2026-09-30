import json
import threading

from sparksdb import saved_queries, store


def test_saved_queries_save_update_delete(config_home):
    created = saved_queries.save_query({"connId": "c1", "name": "a", "sql": "select 1"})
    updated = saved_queries.save_query(
        {"id": created["id"], "connId": "c1", "name": "b", "sql": "select 2"}
    )

    assert updated == {"id": created["id"], "connId": "c1", "name": "b", "sql": "select 2"}
    assert json.loads((config_home / "saved_queries.json").read_text()) == [updated]

    saved_queries.delete_query(created["id"])
    assert saved_queries.list_queries() == []


NEW_CONNECTION = {"name": "local", "host": "h", "database": "d", "user": "u", "password": "s3cret"}


def test_connection_save_edit_without_password_delete(config_home, memory_keyring):
    saved = store.save_connection(dict(NEW_CONNECTION))
    assert saved == {
        "id": saved["id"], "name": "local", "host": "h", "port": 5432,
        "database": "d", "user": "u", "ssl": False, "encrypted": True,
    }

    edited = store.save_connection(
        {"id": saved["id"], "name": "renomeada", "host": "h", "port": 6543, "database": "d", "user": "u"}
    )
    assert edited["encrypted"] is True
    assert json.loads((config_home / "connections.json").read_text()) == [edited]
    assert store.get_connection_with_password(saved["id"]) == (edited, "s3cret")

    store.delete_connection(saved["id"])
    assert store.list_connections() == []
    assert memory_keyring.passwords == {}

    (config_home / "connections.json").write_text("{corrompido")
    assert store.list_connections() == []


def test_password_falls_back_to_plaintext_when_keyring_fails(config_home, failing_keyring):
    saved = store.save_connection(dict(NEW_CONNECTION))

    assert saved["encrypted"] is False
    assert json.loads((config_home / "connections-fallback.json").read_text()) == {saved["id"]: "s3cret"}
    assert store.get_connection_with_password(saved["id"])[1] == "s3cret"


def test_concurrent_saves_keep_every_record(config_home):
    threads = [
        threading.Thread(target=saved_queries.save_query, args=({"connId": "c1", "name": str(i), "sql": "select 1"},))
        for i in range(40)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(saved_queries.list_queries()) == 40
