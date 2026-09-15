from app.core.utils import sanitize_filename


def test_clean_filename_unchanged():
    assert sanitize_filename("contacts.csv") == "contacts.csv"


def test_path_traversal_sanitized():
    result = sanitize_filename("../../../etc/passwd")
    assert "/" not in result
    assert ".." not in result
    assert result.startswith("etc_passwd") or result.startswith("_")


def test_spaces_and_special_chars():
    assert sanitize_filename("my file (1).csv") == "my_file__1_.csv"


def test_only_dots_returns_unnamed():
    assert sanitize_filename("...") == "unnamed"


def test_very_long_name_truncated():
    result = sanitize_filename("a" * 2000)
    assert len(result) <= 200
