
import hashlib
import json

import requests

from .catalog import Catalog


class Lightroom:
    """
    Implementation of Lightroom API.
    See https://www.adobe.io/apis/creativecloud/lightroom/apidocs.html
    """

    def __init__(self, api_key, token, base='https://lr.adobe.io/v2/'):
        self.api_key = api_key
        self.token = token
        self.base = base

    #
    # Helpers
    #

    def __process_response__(self, resp):
        resp.raise_for_status()
        # remove the `while(1) {}`...
        result = resp.text.replace('while (1) {}', '')
        if not result:
            return {}
        else:
            return json.loads(result)

    def __authed_headers__(self):
        return {
            'X-API-Key': self.api_key,
            'Authorization': 'Bearer ' + self.token
        }

    def __json_header__(self):
        return {
            'Content-Type': 'application/json'
        }

    def __get_shah_of_file__(self, file_path):
        with open(file_path, 'rb') as f:
            bytes = f.read()
            readable_hash = hashlib.sha256(bytes).hexdigest()
        return readable_hash

    def __get_mime_type__(self, file_path):
        import magic
        mime = magic.from_file(file_path, mime=True)

        # Note: on most versions of libmagic, RAW files are incorrectly considered tiffs...
        if mime == 'image/tiff':
            mime = 'application/octet-stream'
        return mime

    #
    # Abstractions over http requests
    #

    def _get(self, path, params=None, **kwargs):
        headers = {
            **kwargs.pop('headers', {}),
            **self.__authed_headers__()
        }
        kwargs['headers'] = headers
        return self.__process_response__(requests.get(url=self.base + path, params=params, **kwargs))

    def _put(self, path, data=None, **kwargs):
        headers = {
            **kwargs.pop('headers', {}),
            **self.__authed_headers__()
        }
        kwargs['headers'] = headers
        return self.__process_response__(requests.put(url=self.base + path, data=data, **kwargs))

    #
    # Health
    #

    def health(self):
        return self._get('health')

    #
    # Accounts
    #

    def account(self):
        return self._get('account')

    #
    # Catalog
    #

    def catalog(self):
        return self._get('catalog')

    def catalog_api(self):
        return Catalog(self, self.catalog())
