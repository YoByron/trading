# Known Issues

## Python 3.14 Compatibility

There is a known compatibility issue between Python 3.14 and `langchain-core` related to `urllib3.packages.six.moves`. This affects the import of deepagents tools.

**Workaround**: Use Python 3.11, 3.12, or 3.13 for the deepagents integration.

**Status**: Waiting for langchain-core to add Python 3.14 support.

## Dependency Conflicts

- `alpaca-trade-api` requires `urllib3<1.25`
- `clickhouse-connect` requires `urllib3>=1.26`

These are non-blocking warnings and the system should function correctly with `urllib3==1.24.3`.

