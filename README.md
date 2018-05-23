# django-nameko

![build status](https://api.travis-ci.org/and3rson/django-nameko.svg)

Django wrapper for [Nameko] microservice framework.

# How to use

```python
from django_nameko import get_pool           

# Within some view or model:
with get_pool().next() as rpc:
    rpc.mailer.send_mail(foo='bar')
```

# Installation

```sh
pip install django-nameko
```

# Configuration

```python
# Config to be passed to ClusterRpcProxy 
NAMEKO_CONFIG = { 
    'AMQP_URL': 'amqp://127.0.0.1:5672/'
}  

# Number of proxies to create
NAMEKO_POOL_SIZE = 4
# Set timeout for RPC
NAMEKO_TIMEOUT = 15  # timeout 15 seconds
# Add this dictionary to context_data of every RPC
NAMEKO_CONTEXT_DATA = {
    'hostname': "my.example.com"
}

```

# Credits
Thanks to guys who made an awesome [Nameko] framework.

[Nameko]: https://github.com/onefinestay/nameko
