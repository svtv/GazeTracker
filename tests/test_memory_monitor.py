from src.memory_monitor import format_bytes, process_rss_bytes


def test_format_bytes():
    assert format_bytes(None) == "unavailable"
    assert format_bytes(1024) == "1.0 KiB"
    assert format_bytes(5 * 1024 * 1024) == "5.0 MiB"


def test_process_rss_is_positive_when_supported():
    rss = process_rss_bytes()
    assert rss is None or rss > 0
