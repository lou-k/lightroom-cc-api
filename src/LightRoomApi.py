
import datetime
import hashlib
import json
import ntpath
import socket
import uuid

import requests


class LightRoomApi:
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

    def __api_key_headers__(self):
        return {'X-API-Key': self.api_key}

    def __authed_headers__(self):
        return {
            **self.__api_key_headers__(),
            'Authorization': 'Bearer ' + self.token
        }

    def __json_header__(self):
        return {
            'Content-Type': 'application/json'
        }

    def __get_uuid(self):
        return str(uuid.uuid4()).replace('-', '')

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
    # Health
    #

    def health(self):
        return self.__process_response__(requests.get(self.base + 'health', headers=self.__api_key_headers__()))

    #
    # Accounts
    #

    def account(self):
        return self.__process_response__(requests.get(self.base + 'account', headers=self.__authed_headers__()))

    #
    # Catalog
    #

    def catalog(self):
        return self.__process_response__(requests.get(self.base + 'catalog', headers=self.__authed_headers__()))

    #
    # Assets
    #

    # TODO
    # def post_renditions()

    def put_revision(self, catalog_id, asset_id, revision_id, body, sha256=None):
        headers = {
            **self.__authed_headers__(),
            **self.__json_header__()
        }
        if sha256:
            headers['If-None-Match'] = sha256

        return self.__process_response__(requests.put(
            url=self.base +
            f'catalogs/{catalog_id}/assets/{asset_id}/revisions/{revision_id}',
            data=json.dumps(body),
            headers=headers
        ))

    def put_master(self, catalog_id, asset_id, revision_id, data, content_type):
        headers = {
            **self.__authed_headers__(),
            'Content-Type': content_type
        }
        return self.__process_response__(requests.put(
            url=self.base +
            f'catalogs/{catalog_id}/assets/{asset_id}/revisions/{revision_id}/master',
            data=data,
            headers=headers
        ))

    def renditions(self, catalog_id, asset_id, rendition_type):
        return self.__process_response__(requests.get(
            self.base +
            f'catalogs/{catalog_id}/assets{asset_id}/renditions/{rendition_type}',
            headers=self.__authed_headers__()
        ))

    def assets(self, catalog_id, **kwargs):
        if 'next' in kwargs:
            href = f'catalogs/{catalog_id}/' + kwargs.pop('next')['href']
        else:
            href = f'catalogs/{catalog_id}/assets'

        return self.__process_response__(requests.get(
            self.base + href,
            headers=self.__authed_headers__(),
            params=kwargs
        ))

    def asset(self, catalog_id, asset_id):
        return self.__process_response__(requests.get(
            self.base + f'catalogs/{catalog_id}/assets/{asset_id}',
            headers=self.__authed_headers__()
        ))

    #
    # Albums
    #

    def put_album(self, catalog_id, album_id, body):
        return self.__process_response__(requests.put(
            url=self.base + f'catalogs/{catalog_id}/albums/{album_id}',
            data=json.dumps(body),
            headers=self.__authed_headers__()
        ))

    def album(self, catalog_id, album_id):
        return self.__process_response__(requests.get(
            self.base + f'catalogs/{catalog_id}/albums/{album_id}',
            headers=self.__authed_headers__()
        ))

    def albums(self, catalog_id, **kwargs):
        return self.__process_response__(requests.get(
            self.base + f'catalogs/{catalog_id}/albums',
            headers=self.__authed_headers__(),
            params=kwargs
        ))

    def put_asset_to_album(self, catalog_id, album_id, body):
        return self.__process_response__(requests.put(
            url=self.base + f'catalogs/{catalog_id}/albums/{album_id}/assets',
            data=json.dumps(body),
            headers=self.__authed_headers__()
        ))

    def list_assets(self, catalog_id, album_id, **kwargs):
        return self.__process_response__(requests.get(
            url=self.base + f'catalogs/{catalog_id}/albums/{album_id}/assets',
            headers=self.__authed_headers__(),
            params=kwargs
        ))

    #
    # higher level helpers
    #

    def create_new_revision_from_file(self, catalog_id, file_path, sha256=None):

        # Create the asset and reivison id
        asset_id = self.__get_uuid()
        revision_id = self.__get_uuid()

        # timestamp this
        import_timestamp = datetime.datetime.utcnow().isoformat() + 'Z'

        # create the revision
        self.put_revision(
            catalog_id,
            asset_id,
            revision_id,
            body={
                'subtype': 'image',
                'payload': {
                    'captureDate': '0000-00-00T00:00:00',  # Do I neex exif data here?
                    'userCreated': import_timestamp,
                    'userUpdated': import_timestamp,
                    'importSource': {
                        'fileName': ntpath.basename(file_path),
                        'importTimestamp': import_timestamp,
                        'importedOnDevice': socket.gethostname(),
                        'importedBy': self.api_key,
                    }
                }
            },
            sha256=sha256)

        return (asset_id, revision_id)

    def upload_image_file(self, catalog_id, file_path):
        """
        Uploads an image file to lightroom.
        Based on https://github.com/AdobeDocs/lightroom-partner-apis/blob/master/samples/adobe-auth-node/server/lr.js#L55
        """
        # Create a new revision
        asset_id, revision_id = self.create_new_revision_from_file(
            catalog_id, file_path)

        # Figure out the kind of file it is..
        content_type = self.__get_mime_type__(file_path)

        # Upload the original
        with open(file_path, 'rb') as f:
            self.put_master(catalog_id, asset_id,
                            revision_id, f, content_type)

        # return the asset and revision ids
        return asset_id

    def upload_image_file_if_not_exists(self, catalog_id, file_path):
        sha256 = self.__get_shah_of_file__(file_path)

        # lookup existing versions.
        # Note that we could just post it with the `If-None-Match`, but that only works
        # if the subtypes match.
        # This causes a problem when the image was deleted from lightroom: it's subtype becomes
        # 'deleted_image'.
        # By checking existing first, we can see if the file was already uploaded and deleted.
        existing = self.assets(catalog_id, sha256=sha256)['resources']

        if len(existing) > 0:
            return existing[0]
        else:
            asset_id = self.upload_image_file(catalog_id, file_path)
            return self.asset(catalog_id, asset_id)
