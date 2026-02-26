# Installation

## Requirements

- Python ≥ 3.10
- [`pydantic`](https://docs.pydantic.dev/) ≥ 2.0
- [`requests`](https://requests.readthedocs.io/) ≥ 2.28

!!! tip "Use a virtual environment"
    Always install packages inside a virtual environment (`python -m venv .venv`) to avoid conflicts with system packages.

## Core Package

Install the core package with support for Stripe and PayPal stubs:

```bash
pip install merchants
```

## Optional Provider Extras

Some providers depend on additional packages. Install them as extras:

=== "Flow.cl"

    ```bash
    pip install "merchants[flow]"
    ```

    Installs [`pyflowcl`](https://pypi.org/project/pyflowcl/) for [Flow.cl](https://www.flow.cl) payments (Chile).

=== "Khipu"

    ```bash
    pip install "merchants[khipu]"
    ```

    Installs [`khipu-tools`](https://pypi.org/project/khipu-tools/) for [Khipu](https://khipu.com) payments (Chile).

=== "All extras"

    ```bash
    pip install "merchants[flow,khipu]"
    ```

## Development

To work on merchants locally, clone the repository and install in editable mode with dev dependencies:

```bash
git clone https://github.com/mariofix/merchnts-cp.git
cd merchnts-cp
pip install -e ".[dev]"
```

Dev extras include `pytest`, `pytest-cov`, `ruff`, and `responses`.

## Verify Installation

```python
import merchants
print(merchants.__version__)
```

!!! check "Installation successful"
    If no `ImportError` is raised and a version string is printed, merchants is correctly installed.
