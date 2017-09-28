import openshifter.cli

import logging
import os

if os.environ.get("DEBUG", "false") == "true":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    os.environ['LC_ALL']= 'en_US.UTF-8'
    os.environ['LANG'] = 'en_US.UTF-8'
    openshifter.cli.cli()