from sgpt.handlers.chat_handler import ChatHandler


def test_chat_session_ignores_invalid_json_cache():
    session = ChatHandler.chat_session
    chat_id = "_invalid_cache"
    cache_path = session.storage_path / chat_id
    cache_path.write_text("{not valid json")

    assert session.get_messages(chat_id) == []
    assert not session.exists(chat_id)
    cache_path.unlink()
