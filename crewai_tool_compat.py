# Compat shim for CrewAI `tool` decorator across versions
try:
    pass  # preferred (newer)
except Exception:
    try:
        pass  # older
    except Exception:
        try:
            pass  # some distros ship here
        except Exception as e:
            raise ImportError(
                "Missing CrewAI 'tool' decorator; install 'crewai' / 'crewai-tools'."
            ) from e
