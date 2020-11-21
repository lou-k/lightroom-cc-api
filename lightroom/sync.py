import argparse
import json
import logging
import sys
from os import path
from pathlib import Path

import tqdm

from .lightroom import Lightroom


def load_config(config_file):
    if path.exists(config_file):
        with open(config_file, 'r') as f:
            res = json.load(f)
    else:
        logging.warn(f'{config_file} does not exist.')
        res = {}
    return res


def get_key_and_token(args):
    key = args.api_key
    token = args.token
    if (not key) or (not token):
        from_config = load_config(args.config)
        if not key:
            key = from_config.get('api_key')
        if not token:
            token = from_config.get('token')
    return key, token


def is_accepted_type(lr, path):
    content_type = lr.__get_mime_type__(path)
    if content_type.startswith('image'):
        return True
    elif content_type == 'application/octet-stream':
        return True
    else:
        # TODO: add support for video
        return False


def sync():

    logging.basicConfig(
        format='%(levelname)s: %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(
        description='Synchronizes photos to lightroom.')
    parser.add_argument('-k', '--api-key', type=str, default=None,
                        help='The api key to use. If empty, will load it from config_file')
    parser.add_argument('-t', '--token', type=str, default=None,
                        help='The token to use. If empty, will load it from config_file')
    parser.add_argument('-c', '--config', type=str, default='/etc/lr-sync.json',
                        help='A json file containing api_key and token. Defaults to /etc/lr-sync.json')
    parser.add_argument('directory', type=str,
                        help='The directory to scan for media to upload.')

    args = parser.parse_args(sys.argv[1:])

    # Load the credentials
    api_key, token = get_key_and_token(args)
    if not api_key:
        raise ValueError(
            'Could not load api_key. Set it with -k or put it in the config file.')
    if not token:
        raise ValueError(
            'Could not load token. Set it with -t or put it in the config file.')

    # create the api
    lr = Lightroom(api_key, token)

    # get the catalog
    catalog = lr.catalog_api()
    catalog_id = catalog.response['id']
    logging.info(f'Accessed catalog with id {catalog_id}')

    # parse the directory
    files = [p.as_posix()
             for p in Path(args.directory).rglob('*') if not p.is_dir()]
    for file in tqdm.tqdm(files, total=len(files), desc='Processing...'):
        if not is_accepted_type(lr, file):
            logging.warn(f'File {file} is not an image. Skipping..')
        else:
            asset, existed = catalog.upload_image_file_if_not_exists(file)
            asset_id = asset['id']
            if existed:
                logging.info(f'{file} already existed with id {asset_id}')
            else:
                logging.info(f'{file} uploaded to new {asset_id}')
