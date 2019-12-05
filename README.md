# django-nameko

## Travis-CI  [![Coverage Status](https://coveralls.io/repos/github/and3rson/django-nameko/badge.svg)](https://coveralls.io/github/and3rson/django-nameko)
| Branch  | Build status                             |
| ------- | ---------------------------------------- |
| master  | [![Build Status](https://travis-ci.org/and3rson/django-nameko.svg?branch=master)](https://travis-ci.org/and3rson/django-nameko) |
| develop | [![Build Status](https://travis-ci.org/and3rson/django-nameko.svg?branch=develop)](https://travis-ci.org/and3rson/django-nameko) |


Django wrapper for [Nameko] microservice framework.


# support
tested with 

- python 2.7, 3.5, 3.6, 3.7
- django 1.11, 2.0, 2.1, 2.2
- nameko 2.11, 2.12

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
    'AMQP_URI': 'amqp://127.0.0.1:5672/'
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
        'AMQP_URI': 'amqp://',
        'POOL_SIZE': 4,
        'POOL_CONTEXT_DATA': {"common": "multi"},
        'POOL_TIMEOUT': None
    },
    'pool1': {
        'AMQP_URI': 'amqp://pool2',
        'POOL_CONTEXT_DATA': {"name": "pool1", "data": 123},
    },
    'pool2': {
        'AMQP_URI': 'amqp://pool3',
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
# but you can override the rpc context data before call, example below.
# it will auto revert back to POOL_CONTEXT_DATA when exit the with block
with get_pool().next() as rpc:
    rpc._worker_ctx.data['SMTP_SECRET'] = 'SECRETXXX'
    rpc.mailer.send_mail(foo='bar')

# try to call rpc outside of with statement block will raise an AttributeError exception 
rpc.mailer.send_mail(bar='foo')
#   File "/usr/local/lib/python2.7/site-packages/django_nameko/rpc.py", line 69, in __getattr__
#     raise AttributeError(item)
# AttributeError: mailer

# New feature (from 0.7.0):
# To dispatch event to any service event listener, for example you have this nameko service:
from nameko.events import event_handler
class EchoService(object):
    name = 'echo'

    @event_handler("echo", "ping")
    def handle_event(self, payload):
        print("service echo received:%s", payload)
# You can sent an event signal to all service listener like this 
from django_nameko import dispatch
dispatch("echo", "ping", {"payload": {"data": 0}})


```

# contribute

to run the tests:
1. run a local rabbitmq
2. execute tox 
```bash
docker run --rm -p 15672:15672 -p 5672:5672 -p 5671:5671 --name nameko-rabbitmq nameko/nameko-rabbitmq:3.6.6
# open another shell then run
python setup.py test
# to run full test with coverage use
tox 
```

# Credits
Thanks to guys who made an awesome [Nameko] framework.

Maintainers:
  - Andrew Dunai ([@and3rson](https://github.com/and3rson))
  - Vincent Anh Tran ([@tranvietanh1991](https://github.com/tranvietanh1991))

[Nameko]: https://github.com/nameko/nameko
