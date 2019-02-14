# django-nameko

## Travis-CI
| Branch  | Build status                             |
| ------- | ---------------------------------------- |
| master  | [![Build Status](https://travis-ci.org/and3rson/django-nameko.svg?branch=master)](https://travis-ci.org/and3rson/django-nameko) |
| develop | [![Build Status](https://travis-ci.org/and3rson/django-nameko.svg?branch=develop)](https://travis-ci.org/and3rson/django-nameko) |

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
# Each proxy is a single threaded standalone ClusterRpcProxy
NAMEKO_POOL_SIZE = 4
# Set timeout for RPC
NAMEKO_TIMEOUT = 15  # timeout 15 seconds
# Add this dictionary to context_data of every RPC
NAMEKO_CONTEXT_DATA = {
    'hostname': "my.example.com"
}

# Create multiple ClusterRpcProxy pool each one assoiate with a name
# Every pool with pool name different than 'default' will use 'default' pool config as default configuration
NAMEKO_CONFIG={
    'default': {
        'AMQP_URL': 'amqp://',
        'POOL_SIZE': 4,
        'POOL_CONTEXT_DATA': {"common": "multi"},
        'POOL_TIMEOUT': None
    },
    'pool1': {
        'AMQP_URL': 'amqp://pool2',
        'POOL_CONTEXT_DATA': {"name": "pool1", "data": 123},
    },
    'pool2': {
        'AMQP_URL': 'amqp://pool3',
        'POOL_CONTEXT_DATA': {"name": "pool2", "data": 321},
        'POOL_TIMEOUT': 60
    },
    'pool3': {
        'POOL_SIZE': 8,
        'POOL_TIMEOUT': 60
    }
}
# Use multi pool by putting pool name in get_pool(..)
from django_nameko import get_pool

with get_pool('pool1').next() as rpc:
    rpc.mailer.send_mail(foo='bar')
    
# call get_pool() without argument will return the 'default' pool


```

# Credits
Thanks to guys who made an awesome [Nameko] framework.

Maintainers:
  - Andrew Dunai ([@and3rson](https://github.com/and3rson))
  - Vincent Anh Tran ([@tranvietanh1991](https://github.com/tranvietanh1991))

[Nameko]: https://github.com/nameko/nameko
