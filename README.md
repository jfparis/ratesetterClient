RateSetterClient
==========

Client library to access to the RateSetter, peer to peer lending platform

# Installation

This module is available on PyPi so it can be installed by using the pip command

```
    pip install ratesetterClient
```

# Usage

```python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function
from ratesetterclient import RateSetterClient
from pprint import pprint

def main():
    client = RateSetterClient("email@email.com", "password", natural=False)
    client.connect()
    pprint(client.get_market_rates())
    pprint(client.get_provision_fund())
    pprint(client.get_account_summary())
    pprint(client.get_portfolio_summary())
    pprint(client.get_market(client.markets.monthly))

    client.disconnect()


if __name__ == "__main__":
    main()

```