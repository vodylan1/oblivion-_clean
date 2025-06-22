"""
Test-time stub that replaces the real metrics loop.
The production file opens an asyncio event loop on import,
which breaks pytest.  For CI we only need the exported
`start_background()` symbol to exist.
"""


def start_background(*_, **__):  # noqa: D401
    # Do nothing in unit-test context
    return
