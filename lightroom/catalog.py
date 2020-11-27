import datetime
import json
import ntpath
import socket
import uuid


class Catalog:

    def __init__(self, lightroom, response):
        self.lr = lightroom
        self.catalog_id = response['id']
        self.response = response

    def __get_uuid(self):
        return str(uuid.uuid4()).replace('-', '')

    #
    # Assets
    #

    # TODO
    # def post_renditions()

    def put_revision(self, asset_id, revision_id, body, sha256=None):
        headers = self.lr.__json_header__()
        if sha256:
            headers['If-None-Match'] = sha256

        return self.lr._put(
            path=f'catalogs/{self.catalog_id}/assets/{asset_id}/revisions/{revision_id}',
            data=json.dumps(body),
            headers=headers
        )

    def put_master(self, asset_id, revision_id, data, content_type):
        headers = {'Content-Type': content_type}
        return self.lr._put(
            path=f'catalogs/{self.catalog_id}/assets/{asset_id}/revisions/{revision_id}/master',
            data=data,
            headers=headers
        )

    def renditions(self, asset_id, rendition_type):
        return self.lr._get(f'catalogs/{self.catalog_id}/assets{asset_id}/renditions/{rendition_type}')

    def assets(self, **kwargs):
        if 'next' in kwargs:
            href = f'catalogs/{self.catalog_id}/' + kwargs.pop('next')['href']
        else:
            href = f'catalogs/{self.catalog_id}/assets'

        return self.lr._get(href, params=kwargs)

    def asset(self, asset_id):
        return self.lr._get(f'catalogs/{self.catalog_id}/assets/{asset_id}')

    #
    # Albums
    #

    def put_album(self, album_id, body):
        return self.lr._put(
            path=f'catalogs/{self.catalog_id}/albums/{album_id}',
            data=json.dumps(body)
        )

    def album(self, album_id):
        return self.lr._get(f'catalogs/{self.catalog_id}/albums/{album_id}')

    def albums(self, **kwargs):
        return self.lr._get(f'catalogs/{self.catalog_id}/albums', params=kwargs)

    def put_asset_to_album(self, album_id, body):
        return self.lr._put(
            path=f'catalogs/{self.catalog_id}/albums/{album_id}/assets',
            data=json.dumps(body)
        )

    def list_assets(self, album_id, **kwargs):
        return self.lr._get(f'catalogs/{self.catalog_id}/albums/{album_id}/assets', params=kwargs)

    #
    # higher level helpers
    #

    def create_new_revision_from_file(self, file_path, content_type, sha256=None):

        # Create the asset and reivison id
        asset_id = self.__get_uuid()
        revision_id = self.__get_uuid()

        # timestamp this
        import_timestamp = datetime.datetime.utcnow().isoformat() + 'Z'

        # figure out the subtype
        subtype = 'image'
        if content_type.startswith('video'):
            subtype = 'video'

        # create the revision
        self.put_revision(
            asset_id,
            revision_id,
            body={
                'subtype': subtype,
                'payload': {
                    'captureDate': '0000-00-00T00:00:00',  # Do I neex exif data here?
                    'userCreated': import_timestamp,
                    'userUpdated': import_timestamp,
                    'importSource': {
                        'fileName': ntpath.basename(file_path),
                        'importTimestamp': import_timestamp,
                        'importedOnDevice': socket.gethostname(),
                        'importedBy': self.lr.session.headers['X-API-Key'],
                    }
                }
            },
            sha256=sha256)

        return (asset_id, revision_id)

    def upload_media_file(self, file_path):
        """
        Uploads an image file to lightroom.
        Based on https://github.com/AdobeDocs/lightroom-partner-apis/blob/master/samples/adobe-auth-node/server/lr.js#L55
        """

        # Figure out the kind of file it is..
        content_type = self.lr.__get_mime_type_mapped__(file_path)

        # Create a new revision
        asset_id, revision_id = self.create_new_revision_from_file(
            file_path, content_type)

        # Upload the original
        with open(file_path, 'rb') as f:
            self.put_master(asset_id, revision_id, f, content_type)

        # return the asset and revision ids
        return asset_id

    def upload_media_file_if_not_exists(self, file_path):
        sha256 = self.lr.__get_shah_of_file__(file_path)

        # lookup existing versions.
        # Note that we could just post it with the `If-None-Match`, but that only works
        # if the subtypes match.
        # This causes a problem when the image was deleted from lightroom: it's subtype becomes
        # 'deleted_image'.
        # By checking existing first, we can see if the file was already uploaded and deleted.
        existing = self.assets(sha256=sha256)['resources']

        if len(existing) > 0:
            return existing[0], True
        else:
            asset_id = self.upload_media_file(file_path)
            return self.asset(asset_id), False
