
import hashlib
import json
import magic

import requests

from .catalog import Catalog


class Lightroom:
    """
    Implementation of Lightroom API.
    See https://www.adobe.io/apis/creativecloud/lightroom/apidocs.html
    """

    def __init__(self, api_key, token, base='https://lr.adobe.io/v2/', session = None):
        if session is None:
            self.session = requests.Session()
        else:
            self.session = session
        self.session.headers.update({
            'X-API-Key': api_key,
            'Authorization': 'Bearer ' + token
        })
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
        return magic.from_file(file_path, mime=True)

    def __get_mime_type_mapped__(self, file_path):
        mime = self.__get_mime_type__(file_path)

        # Note: on most versions of libmagic, RAW files are incorrectly considered tiffs...
        if mime == 'image/tiff':
            mime = 'application/octet-stream'
        return mime

    #
    # Abstractions over http requests
    #

    def _get(self, path, params=None, **kwargs):
        return self.__process_response__(self.session.get(url=self.base + path, params=params, **kwargs))

    def _put(self, path, data=None, **kwargs):
        return self.__process_response__(self.session.put(url=self.base + path, data=data, **kwargs))

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
