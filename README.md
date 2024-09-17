# Merchants

[![PyPI version](https://badge.fury.io/py/merchants.svg)](https://badge.fury.io/py/merchants)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/merchants.svg)](https://pypi.org/project/merchants/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Downloads](https://pepy.tech/badge/merchants)](https://pepy.tech/project/merchants)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A unified payment processing toolkit for FastAPI applications, inspired by django-payments.

## Overview

Merchants is an all-in-one payment processing solution designed to integrate seamlessly with FastAPI applications. This
modular payment integration system aims to simplify the implementation of various payment gateways and provide a
flexible interface for handling different payment methods.

## Features

- Easy integration with FastAPI applications
- Support for multiple payment gateways
- Customizable payment workflows
- Webhook handling for payment status updates
- Extensible architecture for adding new payment providers
- Unified API across different payment services

## Installation

```bash
poetry add fastapi-merchants
```

## Quick Start

```python
from fastapi import FastAPI
from fastapi_merchants import Merchants

app = FastAPI()
merchants = Merchants(app)

# Configure your payment providers
merchants.add_provider("stripe", api_key="your_stripe_api_key")
merchants.add_provider("paypal", client_id="your_paypal_client_id", client_secret="your_paypal_client_secret")

# Use Merchants in your routes
@app.post("/create-payment")
async def create_payment(amount: float, currency: str, provider: str):
    return await merchants.create_payment(amount, currency, provider)
```

## Documentation

For detailed documentation, please visit [our documentation site](https://mariofix.github.io/fastapi-merchants).

## License

Merchants is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements

This project was inspired by the django-payments library and aims to provide similar functionality for FastAPI
applications, some parts were made with Claude and/or ChatGPT.

## Changelog

See the [CHANGELOG](CHANGELOG) file for more details.
