#!/usr/bin/python3

import argparse
import os

import _srm_version
import srm_util

###############################################################
# Functions to process commands followed by the function that
# provides help for that command
###############################################################
def _cmd_get(args):
    if len(args) == 0:
        srm_util.err('The get command needs atleast one resource name')
        srm_util.info(_help_get())
        exit(1)
    cur_environ = os.environ.copy()
    resource_defs = srm_util.env().resource_defs
    added = []
    for resource_name in args:
        if resource_name in added:
            continue
        resource_def = srm_util.get_resource_def(resource_name)
        if resource_def is None:
            srm_util.warn('Ignoring {} because a resource definition file was not found'.format(resource_name))
            continue
        # Call the 'get' function on the resource definition script to modify the
        # current environment according to its need
        resource_def.get(srm_util, cur_environ)
        added.append(resource_name)
    if added:
        if srm_util.env().args.dry_run:
            srm_util.info('Would enter shell with resources: {}'.format(','.join(added)))
        else:
            srm_util.info('Entering shell with resources: {}'.format(','.join(added)))
            os.execve('/bin/bash', [], env=cur_environ)
    return

def _help_get():
    return '''
Usage: srm get <resource1> <resource2> ...

Use this command to get one or more resources. <resource1> and
<resource2> denote resource names. eg 'gcc/7.2'
'''

def _cmd_info(args):
    return

def _help_info():
    return '''
Usage: srm info <resource>

Use this command to obtain specific information about a particular
resource. eg. 'src info gcc/7.2'
'''

def _cmd_register(args):
    return

def _help_register():
    return '''
Usage: srm register <resource>

Use this command to register a new resource.
eg. 'src register gcc/7.2'
'''

# Table of supported commands initialized with the function that 
# process them.
_CMD_TABLE = {
    'get' : _cmd_get,
    'info' : _cmd_info,
    'register' : _cmd_register
}

_CMD_HELP = {
    'get' : _help_get,
    'info' : _help_info,
    'register' : _help_register
}

def _dispatch_cmd(cmd, args):
    # List all commands
    if cmd == 'list':
        srm_util.info('Listing all supported commands:-')
        for icmd in _CMD_TABLE.keys():
            srm_util.info('   {}'.format(icmd))
    elif cmd == 'help':
        if len(args) == 0:
            srm_util.err('help command expects a command name. Example "srm help get"')
            srm_util.info('Did you mean to do "srm --help"?')
            exit(1)
        for iarg in args:
            if iarg in _CMD_HELP:
                helptext = _CMD_HELP[iarg]()
                srm_util.info(helptext)
            else:
                srm_util.warn('Skipping {} because there is no installed help for this command'.format(iarg))
    else:
        if cmd not in _CMD_TABLE:
            srm_util.err('{} is not a recognized command'.format(cmd))
            exit(1)
        srm_util.dbg('Dispatching command: "{}" with arguments {}'.format(cmd, args))
        _CMD_TABLE[cmd](args)
    return


def main():
    p = argparse.ArgumentParser(description='Software Resource Manager {}'.format(_srm_version.VERSION_STR))
    p.add_argument(
        '-l', '--log',
        choices=['debug', 'info'],
        default='info',
        help='Controls the output verbosity'
    )
    p.add_argument(
        '-c', '--config',
        help='Path to the json file specifying initial config'
    )
    p.add_argument(
        '-d', '--dry-run',
        dest='dry_run',
        action='store_true',
        help='Dry run the resource loader. Do not actually enter a new shell. Useful for unit testing'
    )
    p.add_argument(
        'cmd',
        nargs='?',
        help='The command to run. Try "srm list cmd" to list all commands'
    )
    p.add_argument(
        'args',
        nargs='*',
        help=
        'Arguments to pass to the specific command. Try "srm help <cmd>" for help on the specific command'
    )

    args = p.parse_args()

    # If no arguments were provided, just print the help and exit
    if args.cmd is None:
        p.print_help()
        exit()

    srm_util.init(args)

    _dispatch_cmd(args.cmd, args.args)

if __name__ == '__main__':
    main()
