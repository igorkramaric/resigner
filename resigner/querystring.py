import time
import json

try:
    # python >= 3
    from urllib.parse import urlencode, parse_qsl

except ImportError:
    # python < 3
    from urlparse import parse_qsl
    from urllib import urlencode

from django.core.signing import Signer

from resigner.models import ApiKey


class ValidationError(Exception):
    pass

def _generate_signature(params, secret, timestamp):
    signer = Signer(key=secret)
    encoded_params = json.dumps(params, sort_keys=True)
    return signer.signature(":".join([timestamp, encoded_params]))

def sign(params, key, secret):
    params = {str(k): str(v) for (k, v) in list(params.items())}
    timestamp = str(int(time.time()))

    params["signature"] = _generate_signature(params, secret, timestamp)
    params["key"] = key
    params["timestamp"] = timestamp

    return urlencode(params)

def validate(querystring, max_age=60*60):
    params = dict(parse_qsl(querystring))

    for key in ["timestamp", "key", "signature", ]:
        if key not in params:
            raise ValidationError("{0} must exist".format(key))

    key = params.pop("key")
    signature = params.pop("signature")

    timestamp = params.pop("timestamp")
    time_stamp_expired = int(timestamp) + max_age


    if time.time() > time_stamp_expired:
        raise ValidationError("Timestamp Expired")

    try:
        api_key = ApiKey.objects.get(key=key)
    except ApiKey.DoesNotExist:
        raise ValidationError("Key does not exist")

    new_signature = _generate_signature(params, api_key.secret, timestamp)

    if new_signature != signature:
        raise ValidationError("Your signature was invalid")

    return True