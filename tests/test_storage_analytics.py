from placepal import analytics, storage


def make_session(items):
    return storage.new_session("Data Analyst", "Medium", "gemma3:4b", items)


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "s.json"
    session = make_session([{"topic": "SQL", "score": 6}])
    storage.save_session(session, path)
    storage.save_session(make_session([{"topic": "SQL", "score": 8}]), path)
    loaded = storage.load_sessions(path)
    assert len(loaded) == 2 and loaded[0]["id"] == session["id"]


def test_corrupt_file_is_preserved_not_destroyed(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("{not json", encoding="utf-8")
    assert storage.load_sessions(path) == []
    assert (tmp_path / "s.corrupt").exists()


def test_clear_sessions(tmp_path):
    path = tmp_path / "s.json"
    storage.save_session(make_session([{"topic": "SQL", "score": 6}]), path)
    storage.clear_sessions(path)
    assert storage.load_sessions(path) == []


def test_topic_scores_and_weakest():
    sessions = [
        make_session([{"topic": "SQL", "score": 8}, {"topic": "DSA", "score": 3}]),
        make_session([{"topic": "SQL", "score": 6}, {"topic": "DSA", "score": 5}]),
    ]
    scores = analytics.topic_scores(sessions)
    assert scores["SQL"] == {"average": 7.0, "attempts": 2}
    assert analytics.weakest_topics(sessions, limit=1) == [("DSA", 4.0)]


def test_new_session_average():
    assert make_session([{"score": 4}, {"score": 8}])["avg_score"] == 6.0
