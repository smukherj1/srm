import logging
import os
import json
import argparse
import hashlib
import importlib
import importlib.util
import importlib.machinery

class SrmEnv(object):
    """
    Convenience class caching references to frequently used
    utilities like command line arguments, configuration info
    etc
    """

    def __init__(self):
        # Command line arguments to srm
        self._args = None
        # Message logger
        self._logger = None
        ########################################################
        # Info from the configuration json file
        ########################################################
        # Path to database with cached resource info
        self._db_path = None
        # Path to resource definition python scripts
        self._resource_defs = None
        ########################################################
        # Map from path to a python file to the module 
        self._cached_modules = {}

    def set_args(self, args):
        assert self._args is None
        assert isinstance(args, argparse.Namespace)
        self._args = args

    def set_logger(self, logger):
        assert self._logger is None
        assert isinstance(logger, logging.Logger)
        self._logger = logger
    
    def set_db_path(self, db_path):
        assert self._db_path is None
        assert isinstance(db_path, str)
        self._db_path = db_path

    def set_resource_defs(self, resource_defs):
        assert self._resource_defs is None
        assert isinstance(resource_defs, str)
        self._resource_defs = resource_defs

    def load_script(self, path):
        mod_abs_path = os.path.abspath(path)
        md5_hasher = hashlib.md5()
        md5_hasher.update(mod_abs_path.encode('utf-8'))
        hashed_path = md5_hasher.hexdigest()
        if hashed_path in self._cached_modules:
            return self._cached_modules[hashed_path]
        # Now import the module
        mod = None
        dbg('Attempting to load resource definition: {}, hash: {}'.format(mod_abs_path, hashed_path))
        try:
            import_spec = importlib.util.spec_from_file_location(hashed_path, mod_abs_path) 
            # Only supported in python 3.5 and above
            mod = importlib.util.module_from_spec(import_spec)
            import_spec.loader.exec_module(mod)
        except AttributeError:
            # Use older python3 import machinery
            loader = importlib.machinery.SourceFileLoader(hashed_path, mod_abs_path)
            mod = loader.load_module()
        self._cached_modules[hashed_path] = mod
        return mod
 

    @property
    def args(self):
        return self._args

    @property
    def logger(self):
        """
        NOT TO BE USED OUTSIDE srm_util. Use the dbg, info, warn, crit,
        and err functions in this module instead
        """
        return self._logger

    @property
    def db_path(self):
        return self._db_path

    @property
    def resource_defs(self):
        return self._resource_defs

_env = None


def init(args):
    global _env
    if _env is not None:
        raise RuntimeError('Initialization for util has already run!')
    _env = SrmEnv()
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%y/%m/%d %H:%M:%S')
    _env.set_args(args)
    logger = logging.getLogger('srm')
    _env.set_logger(logger)
    if args.log == 'debug':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    _load_initial_config()

def args():
    """
    Get command line arguments
    """
    return _env.args

def dbg(msg):
    """
    Print debug message
    """
    _env.logger.debug(msg)

def info(msg):
    """
    Print info message
    """
    _env.logger.info(msg)

def warn(msg):
    """
    Print warning message
    """
    _env.logger.warn(msg)

def crit(msg):
    """
    Print critical warning message
    """
    _env.logger.critical(msg)

def err(msg):
    """
    Print error message
    """
    _env.logger.error(msg)

def env():
    """
    Global access to the environment object
    """
    return _env

def get_resource_def(resource_name):
    path = os.path.join(env().resource_defs, resource_name, 'srm_def.py')
    if not os.path.exists(path):
        return None
    # Now we will try to import the file as is
    mod = None
    try:
        mod = env().load_script(path)
    except Exception as ierr:
        err('Encountered exception trying to load resource definition {}'.format(resource_abs_path))
        info('The exact error was: {}'.format(str(ierr)))
        exit(1)
    return mod
############################################################################
# Functions local to this module
############################################################################
def _get_home_dir():
    if os.name == 'nt':
        return os.environ['userprofile']
    elif os.name == 'posix':
        return os.environ['HOME']
    else:
        raise RuntimeError('Unknown OS {}'.format(os.name))


def _load_initial_config():
    """
    Load settings like path to resource definition scripts and path
    to the SQLite3 database that caches the resource definition
    information
    """
    config_filename = args().config
    home_dir = _get_home_dir()
    if config_filename is None:
        # User didn't specify a config file. Look for the default
        # filename we expect in the OS specific home directory
        config_filename = os.path.join(home_dir, '.srm.json') 
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

        db_path = None
        resource_defs = None

        if 'resource_defs' in config_json:
            resource_defs = config_json['resource_defs']
            if not resource_defs:
                err('resource_defs key in {} was empty'.format(config_filename))
                exit(1)
            dbg("Config specified '{}' for resource_defs".format(resource_defs))
        else:
            resource_defs = os.path.join(home_dir, '.srm.d')
            dbg('Using default value {} for resource definition directory'.format(resource_defs))

        if 'db_path' in config_json:
            db_path = config_json['db_path']
            if not db_path:
                err('db_path key in {} was empty'.format(config_filename))
                exit(1)
            dbg("Config specified '{}' for db_path".format(db_path))
        else:
            db_path = os.path.join(resource_defs, '.srm.sqlite3.db')
            dbg('Using default value {} for resource database path'.format(db_path))

        _env.set_db_path(db_path)
        _env.set_resource_defs(resource_defs)
