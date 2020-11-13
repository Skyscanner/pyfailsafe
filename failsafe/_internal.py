def _do_nothing(*args):
    pass


def _safe_call(callable):
    try:
        callable()
    except Exception:
        pass    # Swallow the exception
