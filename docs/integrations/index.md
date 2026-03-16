# Framework Integrations

merchants-sdk is framework-agnostic — it works anywhere Python runs. For common frameworks, dedicated extension packages wire it in automatically.

## Available integrations

| Package | Framework | Install |
|---|---|---|
| [`flask-merchants`](flask.md) | Flask / Quart | `pip install flask-merchants` |

## Don't see your framework?

merchants-sdk talks plain HTTP through a pluggable [`Transport`](../transport.md). Any framework that can make HTTP requests can use it directly — see the [Quick Start](../quickstart.md) for framework-agnostic usage.
