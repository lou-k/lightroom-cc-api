# lightroom-cc-api
A Python implementation of Adobe's [Creative Cloud Lightroom API](https://www.adobe.io/apis/creativecloud/lightroom/apidocs.html).

## Disclaimer
This project is new and needs a lot of work. Use with caution.. 
See the [issues](https://github.com/lou-k/lightroom-cc-api/issues) page for some low hanging fruit if you have time to contribute :D.

## Pre-Requisities

You'll need to create an application on https://developer.adobe.com/console/ with permissions to access the Lightroom Services. 

Next, you'll need to generate a token using https://github.com/lou-k/adobe-io-auth. This is included as a dependency.

Quickstart:
* Go to the "OAuth Web" page of your app and set the redirect URI to `https://localhost:8443`.
* Download your setup config for your created application.
* Create certs for ssl:
```
$ openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```
* Run the server:
```
adobe-io-server -c <your_downloaded_file.json> -s openid,offline_access,lr_partner_apis -p 8443 -o token.json
```
* Go to the url and authenticate..

## Installation

The python package can be installed via pip/git:
```
pip install git+https://github.com/lou-k/lightroom-cc-api.git@VERSION
```
where `VERSION` is a [relase tag](https://github.com/lou-k/lightroom-cc-api/releases).

In addition, you'll need libmagic. Install via:
* OSX: `brew install libmagic`
* Ubuntu: `sudo apt-get install libmagic`

## API Usage

The `Lightroom` api object has the `health`, `account`, and `catalog` endpoints. 
It also provides catalog api:
```python

from lightroom import Lightroom
lr_api = Lightroom(api_key, token)
catalog = lr_api.catalog_api()
```

The catalog api contains all of of the `assets` and `albums` calls.

```python
# get the assets in the catalog
catalog.assets()
...
```

The catalog api also has two higher-level functions to help you add media to your Lightroom account:
```
# Uploads an image to lightroom
catalog.upload_image_file(path_to_image)

# Uploads an image to lightroom if it's not already in there.
catalog.upload_image_file_if_not_exists(path_to_image)
```
