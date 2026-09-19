# Installation

## Requirements

- Python 3.13 or newer.
- A running Herdr instance with an accessible Unix socket.

The distribution name is `herdr-client`. The import package is `herdr_client`.

## Install from PyPI

=== "pip"

    ```bash
    python -m pip install herdr-client
    ```

=== "uv"

    ```bash
    uv add herdr-client
    ```

## Verify the installation

```bash
python -c "import herdr_client; print(herdr_client.__name__)"
```

The client does not start Herdr for you. Start Herdr separately, then follow the
[socket configuration guide](../guides/client-configuration.md).

## Development installation

```bash
git clone https://github.com/mariotaddeucci/herdr-client.git
cd herdr-client
uv sync --all-groups
```
