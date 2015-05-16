# -*- coding: utf-8 -*-

#  Copyright 2014 Jean-Francois Paris
#
# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function
import ratesetterclient
import logging
import unittest
from decimal import Decimal


def enable_logging():
    """ Enable logging for the ratesetter client
    """
    logger = logging.getLogger('ratesetterclient')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import json
        with open("config.json") as config:
            defaults = json.load( config )
            cls._username = defaults["username"]
            cls._password = defaults["password"]

    def setUp(self):
        self.client = ratesetterclient.RateSetterClient(self._username, self._password, natural=False)
        self.client.connect()

    def tearDown(self):
        self.client.disconnect()
        self.client = None

    def testMarketRates(self):
        rates = self.client.get_market_rates()
        self.assertGreater(rates.monthly, 0, "Rate cannot be 0")
        self.assertGreater(rates.bond_1year, 0, "Rate cannot be 0")
        self.assertGreater(rates.income_3year, 0, "Rate cannot be 0")
        self.assertGreater(rates.income_5year, 0, "Rate cannot be 0")

    def testProvision(self):
        provision = self.client.get_provision_fund()
        self.assertGreater(provision.amount, 0, "Provision amount cannot be 0")
        self.assertGreater(provision.coverage, 0, 'Provision coverage cannot be < 0')

    def testAccount(self):
        account = self.client.get_account_summary()
        self.assertGreater(account.deposited, 0, "Deposited cannot be 0")
        self.assertGreater(account.interest_earned, 0, "interest_earned cannot be 0")
        self.assertGreater(account.total, 0, "total cannot be 0")

    def testPortfolio(self):
        portfolio = self.client.get_portfolio_summary()
        bond = portfolio.bond_1year
        self.assertGreater(bond.amount, 0, "Bond is lent")
        self.assertGreater(bond.average_rate, 0, "Bond is lent")
        income_3year = portfolio.income_3year
        self.assertGreater(income_3year.amount, 0, "3 year is lent")
        self.assertGreater(income_3year.average_rate, 0, "3 year is lent")
        income_5year = portfolio.income_5year
        self.assertGreater(income_5year.amount, 0, "5 year is lent")
        self.assertGreater(income_5year.average_rate, 0, "5 year is lent")

    def testMarkets(self):
        market = self.client.get_market(self.client.markets.monthly)
        self.assertGreater(len(market), 0, "Market is empty")
        market = self.client.get_market(self.client.markets.bond_1year)
        self.assertGreater(len(market), 0, "Market is empty")
        market = self.client.get_market(self.client.markets.income_3year)
        self.assertGreater(len(market), 0, "Market is empty")
        market = self.client.get_market(self.client.markets.income_5year)
        self.assertGreater(len(market), 0, "Market is empty")

    def testFailedLending(self):
        self.assertRaises(ratesetterclient.api.RateSetterException, self.client.place_order, self.client.markets.monthly, 5, 0.10)

    def testLending(self):
        old_orders = self.client.list_orders(self.client.markets.monthly)
        self.client.place_order(self.client.markets.monthly, 10, 0.10)
        new_orders = self.client.list_orders(self.client.markets.monthly)
        self.assertEqual(len(old_orders)+1, len(new_orders))
        cancel = None
        for order in new_orders:
            if order.amount == Decimal('10.00') and order.rate == Decimal('0.10'):
                cancel = order
        self.assertIsNotNone(cancel, "Could not identify order in the list")
        self.client.cancel_order(order)


def suite():
    enable_logging()
    s = unittest.TestSuite()
    load_from = unittest.defaultTestLoader.loadTestsFromTestCase
    s.addTests(load_from(TestClient))
    return s


if __name__ == "__main__":
    t = unittest.TextTestRunner()
    t.run(suite())


