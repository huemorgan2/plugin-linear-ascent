# Regular package so `from tests.test_faction_hall import ...` resolves to
# THIS tests dir even when the shared venv also has luna's own `tests`
# package installed (regular packages beat namespace portions on sys.path).
