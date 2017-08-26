import logging
import os
import json

_initialized = False
_args = None
_logger = None



def init(args):
    global _initialized
    if _initialized:
        raise RuntimeError('Initialization for util has already run!')
    _initialized = True
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%y/%m/%d %H:%M:%S')
    global _args
    _args = args
    global _logger
    _logger = logging.getLogger('srm')
    if args.log == 'debug':
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.INFO)
    _load_initial_config()

def args():
    """
    Get command line arguments
    """
    return _args

def dbg(msg):
    """
    Print debug message
    """
    _logger.debug(msg)

def info(msg):
    """
    Print info message
    """
    _logger.info(msg)

def warn(msg):
    """
    Print warning message
    """
    _logger.warn(msg)

def crit(msg):
    """
    Print critical warning message
    """
    _logger.critical(msg)

def err(msg):
    """
    Print error message
    """
    _logger.error(msg)

############################################################################
# Functions local to this module
############################################################################

def _load_initial_config():
    """
    Load settings like path to resource definition scripts and path
    to the SQLite3 database that caches the resource definition
    information
    """
    config_filename = _args.config
    if config_filename is None:
        # User didn't specify a config file. Look for the default
        # filename we expect in the OS specific home directory
        config_filename = '.srm.json'
        if os.name == 'nt':
            config_filename = os.path.join(
                    os.environ['userprofile'],
                    config_filename)
        elif os.name == 'posix':
            config_filename = os.path.join(
                    os.environ['HOME'],
                    config_filename
                    )
    if not os.path.isfile(config_filename):
        err("Did not find expected configuration file '{}'".format(config_filename))
        exit(1)
    dbg('Parsing configuration file {}'.format(config_filename))
    config_json = None
    with open(config_filename) as json_fp:
        try:
            config_json = json.load(json_fp)
        except json.JSONDecodeError as jerr:
            err('Encountered fatal error "{}" while parsing {}'.format(str(jerr), config_filename))
            exit(1)
