# Instalación

## Requisitos

- Python ≥ 3.10
- [`pydantic`](https://docs.pydantic.dev/) ≥ 2.0
- [`requests`](https://requests.readthedocs.io/) ≥ 2.28

!!! tip "Usa un entorno virtual"
    Siempre instala paquetes dentro de un entorno virtual (`python -m venv .venv`) para evitar conflictos con los paquetes del sistema.

## Paquete Principal

Instala el paquete principal con soporte para Stripe y PayPal:

```bash
pip install merchants
```

## Extras de Proveedores Opcionales

Algunos proveedores dependen de paquetes adicionales. Instálalos como extras:

=== "Flow.cl"

    ```bash
    pip install "merchants[flow]"
    ```

    Instala [`pyflowcl`](https://pypi.org/project/pyflowcl/) para pagos en [Flow.cl](https://www.flow.cl) (Chile).

=== "Khipu"

    ```bash
    pip install "merchants[khipu]"
    ```

    Instala [`khipu-tools`](https://pypi.org/project/khipu-tools/) para pagos en [Khipu](https://khipu.com) (Chile).

=== "Todos los extras"

    ```bash
    pip install "merchants[flow,khipu]"
    ```

## Desarrollo

Para trabajar en merchants localmente, clona el repositorio e instala en modo editable con las dependencias de desarrollo:

```bash
git clone https://github.com/mariofix/merchnts-cp.git
cd merchnts-cp
pip install -e ".[dev]"
```

Los extras de desarrollo incluyen `pytest`, `pytest-cov`, `ruff` y `responses`.

## Verificar la Instalación

```python
import merchants
print(merchants.__version__)
```

!!! check "Instalación exitosa"
    Si no se lanza ningún `ImportError` y se imprime una cadena de versión, merchants está correctamente instalado.
