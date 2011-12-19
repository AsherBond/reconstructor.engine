#!/usr/bin/env python
import os
from argparse import ArgumentParser
import reconstructor
from reconstructor.distro.debian import Debian
from reconstructor.buildserver import BuildServer
import sys
import logging
try:
    import simplejson as json
except ImportError:
    import json

APP_NAME = 'Reconstructor'
APP_VERSION = reconstructor.__version__
LOG_LEVEL = logging.DEBUG

def setup_logging(level=LOG_LEVEL, log_file=None):
    fmt='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    if log_file:
        logging.basicConfig(level=LOG_LEVEL, \
            filename=log_file, format=fmt)
    else:
        logging.basicConfig(level=LOG_LEVEL, \
            format=fmt)

if __name__=='__main__':
    available_distros = ['debian']
    parser = ArgumentParser(\
        description='{0}\n\nGNU/Linux distribution creator'.format(APP_NAME))
    parser.add_argument("--build-server", action="store_true", dest="build_server", \
        default=False, help="Start Reconstructor BuildServer")
    parser.add_argument("--app-url", action="store", dest="app_url", \
        default=None, help="Reconstructor app url for Build Server")
    parser.add_argument("--key", action="store", dest="key", \
        default=None, help="Key for Build Server")
    parser.add_argument("--output-dir", action="store", dest="output_dir", \
        default=None, help="Output directory for Build Server")
    parser.add_argument("--project", action="store", \
        dest="project", default=None, help="Reconstructor project file")
    parser.add_argument("--name", action="store", \
        dest="name", default="DebianCustom", help="Name of project")
    parser.add_argument("--distro", action="store", dest="distro", \
        help="Distro to build (debian, etc.)")
    parser.add_argument("--arch", action="store", dest="arch", \
        default='i386', help="Architecture (i386 or amd64)")
    parser.add_argument("--version", action="store", \
        dest="version", default='squeeze', help="Version to build (squeeze, wheezy, etc.)")
    parser.add_argument("--packages", action="store", \
        dest="packages", default="", help="Additional packages to add")
    parser.add_argument("--apt-cacher-host", action="store", \
        dest="apt_cacher_host", default=None, help="APT cacher host (i.e. localhost:3142)")
    parser.add_argument("--mirror", action="store", \
        dest="mirror", default=None, help="Mirror to use (default: ftp.us.debian.org/debian)")
    parser.add_argument("--log", action="store", dest="log", default=None, \
        help="Log output to specified file")
    
    args = parser.parse_args()
    setup_logging(log_file=args.log)
    # check for build server option
    if args.build_server:
        # check for config
        if os.path.exists('config.json'):
            logging.debug('Loading config.json')
            try:
                with open('config.json', 'r') as f:
                    cfg = json.loads(f.read())
                if 'apt_cacher_host' in cfg:
                    apt_cacher_host = cfg['apt_cacher_host']
                if 'app_url' in cfg:
                    app_url = cfg['app_url']
                if 'key' in cfg:
                    key = cfg['key']
                if 'mirror' in cfg:
                    mirror = cfg['mirror']
                if 'output_dir' in cfg:
                    output_dir = cfg['output_dir']
            except Exception, e:
                # ignore parse errors
                logging.warn('Unable to parse config.json: {0}'.format(e))
        # get 
        if args.apt_cacher_host:
            apt_cacher_host = args.apt_cacher_host
        if args.app_url:
            app_url = args.app_url
        if args.key:
            key = args.key
        if args.mirror:
            mirror = args.mirror
        if args.output_dir:
            output_dir = args.output_dir
        if not app_url or not key:
            logging.error('You must specify --app-url and --key with --build-server')
            sys.exit(1)
        srv = BuildServer(app_url=app_url, output_dir=output_dir, key=key, \
            apt_cacher_host=apt_cacher_host, mirror=mirror)
        srv.start()
        sys.exit(0)
    prj = None
    if args.project:
        prj = Debian(project=args.project, apt_cacher_host=args.apt_cacher_host, mirror=args.mirror)
    elif args.distro:
        distro = args.distro.lower()
        if distro not in available_distros:
            logging.error('Unknown distro.  Available distros: {0}'.format(\
                ','.join(available_distros)))
            sys.exit(1)
        if distro == 'debian':
            if args.packages.find(',') > -1:
                pkgs = args.packages.split(',')
            else:
                pkgs = [args.packages]
            prj = Debian(arch=args.arch, version=args.version, packages=pkgs, \
                name=args.name, apt_cacher_host=args.apt_cacher_host, mirror=args.mirror)
            
    else:
        parser.print_help()
        logging.error('You must specify a project or distro')
        logging.error('Available distros: {0}'.format(','.join(available_distros)))
        sys.exit(1)
    # build
    if prj:
        prj.build()
        prj.cleanup()
        sys.exit(0)
    parser.print_help()
    sys.exit(0)
    
