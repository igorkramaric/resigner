import time

from future import standard_library
standard_library.install_aliases()

from urllib.parse import urlencode, parse_qsl

from django.test import TestCase

from resigner.models import ApiKey
from resigner import querystring

class TestQueryString(TestCase):

    def setUp(self):
        self.apikey = ApiKey.objects.create()

    def test_kfid_in_querystring(self):
        signed_qs = querystring.sign({"kfid": 1}, key=self.apikey.key, secret=self.apikey.secret)
        self.assertTrue("kfid=1" in signed_qs)

    def test_key_in_querystring(self):
        signed_qs = querystring.sign({"kfid": 1}, key=self.apikey.key, secret=self.apikey.secret)
        self.assertTrue("key={0}".format(self.apikey.key) in signed_qs)

    def test_signature_in_querystring(self):
        signed_qs = querystring.sign({"kfid": 1}, key=self.apikey.key, secret=self.apikey.secret)
        params = dict(parse_qsl(signed_qs))
        self.assertTrue("signature={0}".format(params["signature"]) in signed_qs)

    def test_validate(self):
        signed_qs = querystring.sign(
            {"kfid": 1, "next":"https://www.mediapredict.com"},
            key=self.apikey.key,
            secret=self.apikey.secret,
        )
        self.assertTrue(querystring.validate(str(signed_qs)))

    def test_fail_if_signed_request_expired(self):
        signed_qs = querystring.sign(
            {"kfid": 1},
            key=self.apikey.key,
            secret=self.apikey.secret,
            expiry=0
        )
        self.assertRaises(querystring.ValidationError, querystring.validate, signed_qs)

    def test_fail_if_signed_request_has_wrong_key(self):
        signed_qs = querystring.sign({"kfid": 1}, key="cheese", secret=self.apikey.secret)
        self.assertRaises(querystring.ValidationError, querystring.validate, signed_qs)

    def test_fail_if_signed_request_has_wrong_signature(self):
        signed_qs = querystring.sign({"kfid": 1}, key=self.apikey.key, secret="cheese")
        self.assertRaises(querystring.ValidationError, querystring.validate, signed_qs)
