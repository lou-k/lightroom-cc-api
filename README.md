# lightroom-cc-api
A Python implementation of Adobe's [Creative Cloud Lightroom API](https://www.adobe.io/apis/creativecloud/lightroom/apidocs.html).

## Disclaimer
This project is new and needs a lot of work. Use with caution.. 
See the [issues](https://github.com/lou-k/lightroom-cc-api/issues) page for some low hanging fruit if you have time to contribute :D.

## Pre-Requisities
You'll need two things:

* A lightroom integration api key
* A token for your user.

See the Lightroom's [getting started](https://www.adobe.io/apis/creativecloud/lightroom/docs.html#!quickstart/integration.md) walks you through this, but it's not very inutitive.. [issue #2](https://github.com/lou-k/lightroom-cc-api/issues/2) should add more documentation here.

## Installation

`requirements.txt` has the necessary python packages.

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
