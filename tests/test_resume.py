from placepal import resume


def test_clean_text_collapses_whitespace():
    assert resume.clean_text("a   b\n\n\n\nc\x00d") == "a b\n\nc d"


def test_is_usable():
    assert not resume.is_usable("too short")
    assert resume.is_usable("x" * 100)
