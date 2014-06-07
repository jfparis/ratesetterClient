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
import random
import requests
from lxml import html
from decimal import Decimal
from re import sub
import time

home_page_url = "https://www.ratesetter.com/"
provision_fund_url = "http://www.ratesetter.com/lending/provision_fund.aspx"
market_view_url = "http://www.ratesetter.com/lending/market_view.aspx"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:29.0) Gecko/20100101 Firefox/29.0"


class RateSetterException(Exception):
    pass


class RateSetterClient(object):

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
        """
        self._sign_out_url = tree.xpath('.//div[@id="membersInfo"]//a[contains(text(),"Sign Out")]')[0].get('href')

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

    def get_market_rates(self):
        response = {}
        page = self._session.get(market_view_url)
        tree = html.fromstring(page.text, base_url=page.url)

        span = tree.xpath('.//h3[contains(text(),"Monthly Access")]/following-sibling::div[@class="currentRate"]/span[@class="rateValue"]')
        val = sub(r'[^\d\-.]', '', span[0].text.strip('£ \n\r'))
        response["monthly"] = Decimal(val)/100

        span = tree.xpath('.//h3[contains(text(),"1 Year Bond")]/following-sibling::div[@class="currentRate"]/span[@class="rateValue"]')
        val = sub(r'[^\d\-.]', '', span[0].text.strip('£ \n\r'))
        response["1 year bond"] = Decimal(val)/100

        span = tree.xpath('.//h3[contains(text(),"3 Year Income")]/following-sibling::div[@class="currentRate"]/span[@class="rateValue"]')
        val = sub(r'[^\d\-.]', '', span[0].text.strip('£ \n\r'))
        response["3 year income"] = Decimal(val)/100

        span = tree.xpath('.//h3[contains(text(),"5 Year Income")]/following-sibling::div[@class="currentRate"]/span[@class="rateValue"]')
        val = sub(r'[^\d\-.]', '', span[0].text.strip('£ \n\r'))
        response["5 year income"] = Decimal(val)/100

        return response

    def get_provision_fund(self):
        response = {}
        page = self._session.get(provision_fund_url)
        tree = html.fromstring(page.text, base_url=page.url)

        span = tree.xpath('.//p[contains(text(),"How much is in the Provision Fund")]/span')
        val = sub(r'[^\d\-.]', '', span[0].text.strip('£ \n\r'))
        response["provision_fund"] = Decimal(val)

        span = tree.xpath('.//div[contains(text(),"Coverage Ratio")]/following-sibling::div/span[@class="rateValue"]')
        val = sub(r'[^\d\-.]', '', span[0].text.strip('£ \n\r'))
        response["coverage"] = Decimal(val)/100

        return response
