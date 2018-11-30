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
# Each proxy is a single threaded standalone ClusterRpcProxy
NAMEKO_POOL_SIZE = 4
# Set timeout for RPC
NAMEKO_TIMEOUT = 15  # timeout 15 seconds
# Add this dictionary to context_data of every RPC
NAMEKO_CONTEXT_DATA = {
    'hostname': "my.example.com"
}

# Create multiple ClusterRpcProxy pool each one assoiate with a name
NAMEKO_MULTI_POOL = ['pool1', 'pool2', 'pool3']
# Each pool can have different context_data, 
# note that: NAMEKO_CONTEXT_DATA is also passed to every pool context_data
NAMEKO_MULTI_CONTEXT_DATA={
   'pool1': {"name": "pool1", "data": 123},
   'pool2': {"name": "pool2", "data": 321},
}

# Use multi pool by putting pool name in get_pool(..)
from django_nameko import get_pool

with get_pool('pool1').next() as rpc:
    rpc.mailer.send_mail(foo='bar')
    
# call get_pool() without argument will return the first pool


```

# Credits
Thanks to guys who made an awesome [Nameko] framework.

[Nameko]: https://github.com/nameko/nameko
