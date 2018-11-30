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
```

# Credits
Thanks to guys who made an awesome [Nameko] framework.

Maintainers:
  - Andrew Dunai ([@and3rson](https://github.com/and3rson))
  - Vincent Anh Tran ([@tranvietanh1991](https://github.com/tranvietanh1991))

[Nameko]: https://github.com/onefinestay/nameko
