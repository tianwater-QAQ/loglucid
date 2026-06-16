from loglucid.tokens import estimate


def test_estimate_is_positive_and_grows_with_length():
    assert estimate("") >= 1
    assert estimate("hello world") >= 1
    assert estimate("x" * 400) > estimate("x" * 40)


def test_estimate_uses_tiktoken_if_available_else_heuristic():
    # Either path must return a sane int; we don't require tiktoken to be installed.
    n = estimate("a moderately sized log line msg=hello k=v")
    assert isinstance(n, int) and n > 0
