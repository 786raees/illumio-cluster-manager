# Illumio Cluster Manager
This is a tool to manage illumio clusters. It is designed to be used in a Kubernetes cluster.

## Project Structure
```
illumio-cluster-manager/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── api_client.py        # Base API client class
│   │   ├── vault_client.py      # Vault operations
│   │   └── exceptions.py        # Custom exceptions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── illumio_service.py   # Illumio-specific operations
│   │   └── k8s_service.py       # Kubernetes operations
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py           # Pydantic models for data validation
│   │   └── config.py            # Configuration models
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Logging configuration
│       └── helpers.py           # Common utilities
├── config/
│   ├── __init__.py
│   ├── settings.py              # Environment configuration
│   └── vault_config.py         # Vault-specific settings
├── bin/
│   └── illumio_cluster_manager.py  # CLI entry point
├── tests/
│   ├── __init__.py
│   ├── test_illumio_service.py
│   ├── test_vault_client.py
│   └── conftest.py              # Pytest fixtures
├── docs/
│   ├── API.md                   # API documentation
│   └── DESIGN.md                # Architecture decisions
├── requirements.txt
├── .env.template               # Environment template
└── README.md
```

## Requirements
- Python 3.10+
- Illumio API Key
- Vault Token
- Kubernetes Cluster

## Installation

```
pip install -r requirements.txt
```

## Usage

```
python bin/illumio_cluster_manager.py
```

## Configuration

```
cp .env.template .env
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

