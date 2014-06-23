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

from __future__ import unicode_literals, absolute_import, print_function, division
import random
import requests
from lxml import html
from decimal import Decimal
from re import sub
import time
from collections import OrderedDict, namedtuple

markets_list = (("monthly", "Monthly Access"),
                ("bond_1year", "1 Year Bond"),
                ("income_3year", "3 Year Income"),
                ("income_5year", "5 Year Income"))

account_keys = (("deposited", "Deposited"),
                ("balance", "Balance (Available to lend)"),
                ("promotions", "Promotions"),
                ("on_loan", "Money On Loan"),
                ("interest_earned", "Interest earned"),
                ("on_market", "Money On Market"),
                ("fees", "Fees paid to RateSetter"),
                ("withdrawals", "Withdrawals"),
                ("total", "TOTAL"))


Markets = namedtuple('Markets', ','.join([key for key, _ in markets_list]))
Account = namedtuple('Account', ",".join([key for key, _ in account_keys]))

MarketOffer = namedtuple('MarketOffer', 'rate, amount, nb_offers, cum_amount')
PortfolioRow = namedtuple('PortfolioRow', 'amount, average_rate, on_market')
ProvisionFund = namedtuple('ProvisionFund', 'amount, coverage')

home_page_url = "https://www.ratesetter.com/"
provision_fund_url = "http://www.ratesetter.com/lending/provision_fund.aspx"
market_view_url = "http://www.ratesetter.com/lending/market_view.aspx"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:29.0) Gecko/20100101 Firefox/29.0"


def convert_to_decimal(num):
    """ convert strings to decimal.Decimal() objects, taking into account ratesetter formatting
    conventions

    :param num: a number as per formatted by rate setter website
    :return: decimal.Decimal() representation of num
    """
    val = sub(r'[^\d\(\)\-k.]', '', num.strip('£ \n\r'))
    multiplier = 1
    if val[0] == '(' and val[-1] == ')':
        val = "-" + val.rstrip(')').lstrip('(')
    if val[-1] == 'k':
        multiplier = 1000
        val = val.rstrip('k')
    return Decimal(val) * multiplier


def multiple_iterator(iterator, nb):
    while True:
        res = []
        for each in range(nb):
            res.append(next(iterator))
        yield res


class RateSetterException(Exception):
    pass


class RateSetterClient(object):
    """ A HTML scrapping client for the ratesetter website

    """

    def __init__(self, email, password, natural=True):
        """ Initialise the Rate Setter client

        :param str email: email address for the account
        :param str password: password for the account
        :param boolean natural: when true, the object behave naturally and pauses between requests
        """

        self._email = email
        self._password = password
        self._natural = natural
        self._connected = False

        # if in natural mode, we initiate the random number generator
        if self._natural:
            random.seed()

        self._session = requests.Session()
        self._session.headers = {'User-agent': user_agent}
        self._session.verify = True

        self.markets = Markets(*[key for key, _ in markets_list])
        """Named tuple that holding the name of the different markets

        * monthly: Monthly Access
        * bond_1year: 1 Year Bond
        * income_3year: 3 Year Income
        * income_5year: 5 Year Income
        """

    def _get_http_helper(self):
        """Returns a helper function that allows lxml form processor to post using requests"""

        def helper(method, url, value):
            if not url:
                raise ValueError("cannot submit, no URL provided")
            if method == 'GET':
                return self._session.get(url, value)
            else:
                return self._session.post(url, value)

        return helper

    def _sleep_if_needed(self):
        """Sleep for a random amount of time between 2 and 10 seconds

        This method is used to make our behaviour look more human and avoid overloading Zopa's server
        """
        if self._natural:
            #if in natural mode we sleep for some time
            time.sleep(random.randint(2, 10))

    def _extract_url(self, tree):
        """Extract and save the main urls

        This method shall be called once after connection in order to
        avoid having to seek for the URL at a later stage

        :param tree: lxml tree of the account home page
        """
        self._sign_out_url = tree.xpath('.//div[@id="membersInfo"]//a[contains(text(),"Sign Out")]')[0].get('href')

        # invert the market list
        inv_markets = {v: k for k, v in markets_list}

        self._lending_url = {}
        lending_menu = tree.xpath('.//a[contains(text(),"Lend Money")]/parent::li//following::li[position()<5]/a')
        for each in lending_menu:
            self._lending_url[inv_markets[each.text]] = each.get("href")

    def connect(self):
        """Connect the client to RateSetter
        """

        page = self._session.get(home_page_url)
        tree = html.fromstring(page.text, base_url=page.url)
        self._sleep_if_needed()

        a = tree.xpath('.//div[@class="RegisterBalloon"]/div[@class="balloonButton"]/a[contains(text(),"Login")]')

        page = self._session.get(a[0].attrib['href'])
        tree = html.fromstring(page.text, base_url=page.url)
        form = tree.forms[0]

        # asp.net form require the button that was clicked ..
        form.fields["__EVENTTARGET"] = "ctl00$cphContentArea$cphForm$btnLogin"
        form.fields["ctl00$cphContentArea$cphForm$txtEmail"] = self._email
        form.fields["ctl00$cphContentArea$cphForm$txtPassword"] = self._password

        page = html.submit_form(form, open_http=self._get_http_helper())

        if "login.aspx" in page.url:
            raise RateSetterException("Failed to connect")
        if not "your_lending/summary" in page.url:
            raise RateSetterException("Site has changed")

        self._dashboard_url = page.url
        tree = html.fromstring(page.text, base_url=page.url)
        self._extract_url(tree)

        self._connected = True

    def disconnect(self):
        """ Disconnect the client from RateSetter
        """
        page = self._session.get(self._sign_out_url)

        if not "login.aspx" in page.url:
            raise RateSetterException("Failed to sign out")

        self._connected = False

    def get_account_summary(self):
        """Get a summary of the account

        :return: a namedtuple containing the following field

        * deposited: total amount deposited since the opening of the account
        * balance: Balance (Available to lend)
        * promotions: amount received for promotions
        * on_loan: Money On Loan
        * interest_earned: Interest earned
        * on_market: Money offered on market
        * fees: fees paid to RateSetter
        * withdrawals: total Withdrawals since the opening of the account
        * total: Grand total

        """
        page = self._session.get(self._dashboard_url)
        self._sleep_if_needed()
        tree = html.fromstring(page.text, base_url=page.url)

        response = []
        for key, label in account_keys:
            td = tree.xpath('.//h2/span[contains(text(),"Your Balance Sheet")]/following::td[contains(text(),"{}")]/following-sibling::td[contains(text(),"£")]'.format(label))
            response.append(convert_to_decimal(td[0].text))

        return Account(*response)

    def get_portfolio_summary(self):
        """Get a summary of the connected user portfolio

        :return: a named tuple with the four fields

        * monthly: user portfolio on the Monthly Access market
        * bond_1year: user portfolio on the 1 Year Bond market
        * income_3year: user portfolio on the 3 Year Income market
        * income_5year: user portfolio on the 5 Year Income market

        A user portfolio is in turn a named tuple with the following fields
        * amount: Money on loan in that particular market
        * average_rate: Average lending rate
        * on_market: Money currently on offer on the market
        """
        portfolio_items = []

        page = self._session.get(self._dashboard_url)
        self._sleep_if_needed()
        tree = html.fromstring(page.text, base_url=page.url)

        for key, label in markets_list:
            td = tree.xpath('.//h2/span[contains(text(),"Your Portfolio")]/following::td[contains(text(),"{}")]/parent::tr/descendant::td[contains(@style,"align")]'.format(label))

            amount = convert_to_decimal(td[0].text + td[1].text)
            if not "-" in td[2].text:
                average_rate = convert_to_decimal(td[2].text.rstrip("%"))/100
            else:
                average_rate = Decimal(0)
            on_market = convert_to_decimal(td[3].text + td[4].text)
            portfolio_items.append(PortfolioRow(amount=amount, average_rate=average_rate, on_market=on_market))

        return Markets(*portfolio_items)

    def get_market(self, market):
        """Get the money on offer on a given market

        :param market: one of the name held in self.markets
        :return: a tuple, ordered from the lowest rate to the highest, containing containing \
        named tuples with the following fields

        * rate: the offered rate
        * amount: the total amount on offer at that rate
        * nb_offers: the number of offers
        * cum_amount: cumulative amount on offer at that rate and below
        """
        url = self._lending_url[market]
        url = url.replace("market_view", "market_full").replace("?pid=", "?id=")

        page = self._session.get(url)
        self._sleep_if_needed()

        tree = html.fromstring(page.text, base_url=page.url)
        lending_menu = tree.xpath('.//table[@class="rsTable"]/tr/td')

        iterator = multiple_iterator(iter(lending_menu), 4)
        _ = next(iterator)
        market = []

        for rate, amount, nb_offer, cum_amount in iterator:
            rate = convert_to_decimal(rate.text.strip()) / 100
            amount = convert_to_decimal(amount.text.strip())
            nb_offers = convert_to_decimal(nb_offer.text.strip())
            cum_amount = convert_to_decimal(cum_amount.text.strip())

            market.append(MarketOffer(rate=rate, amount=amount, nb_offers=nb_offers, cum_amount=cum_amount))

        return tuple(reversed(market))

    def place_bid(self, market, amount, rate):
        """ Place a bid to lend money on the market

        :param market: one of the name held in self.markets
        :param amount: Amount to lend in GBP
        :param rate: Offered rate
        """

        page = self._session.get(self._lending_url[market])
        self._sleep_if_needed()

        tree = html.fromstring(page.text, base_url=page.url)
        form = tree.forms[0]

        # asp.net form require the button that was clicked ..
        form.fields["__EVENTTARGET"] = "ctl00$cphContentArea$btnSetRate"
        form.fields["ctl00$cphContentArea$tbAmount"] = str(amount)
        form.fields["ctl00$cphContentArea$tbRate"] = str(rate*100)

        page = html.submit_form(form, open_http=self._get_http_helper())
        self._sleep_if_needed()

        tree = html.fromstring(page.text, base_url=page.url)
        form = tree.forms[0]

        # asp.net form require the button that was clicked ..
        form.fields["__EVENTTARGET"] = "ctl00$cphContentArea$btnOrder"

        page = html.submit_form(form, open_http=self._get_http_helper())

    def get_market_rates(self):
        """Get the rates of the latest matches on the different markets

        :return: a named tuple with the four fields

        * monthly: latest match on the Monthly Access market
        * bond_1year: latest match on the 1 Year Bond market
        * income_3year: latest match on the 3 Year Income market
        * income_5year: latest match on the 5 Year Income market
        """
        rates = []
        page = self._session.get(market_view_url)
        tree = html.fromstring(page.text, base_url=page.url)

        for key, html_label in markets_list:

            span = tree.xpath('.//h3[contains(text(),"{}")]/following-sibling::div[@class="currentRate"]/span[@class="rateValue"]'.format(html_label))
            rates.append(convert_to_decimal(span[0].text)/100)

        return Markets(*rates)

    def get_provision_fund(self):
        """Get the status of the provision fund

        :return: A named tuple with two fields:

        * amount: the amount in the fund in GBP
        * coverage: the coverage ratio of the fund
        """
        page = self._session.get(provision_fund_url)
        tree = html.fromstring(page.text, base_url=page.url)

        span = tree.xpath('.//p[contains(text(),"How much is in the Provision Fund")]/span')
        amount = convert_to_decimal(span[0].text)

        span = tree.xpath('.//div[contains(text(),"Coverage Ratio")]/following-sibling::div/span[@class="rateValue"]')
        coverage = convert_to_decimal(span[0].text)/100

        return ProvisionFund(amount=amount, coverage=coverage)
