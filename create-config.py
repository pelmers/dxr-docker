#!/usr/bin/env python2.7
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import sys
import urlparse
import tempfile
import yaml

from jinja2 import Environment, FileSystemLoader

HERE = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(HERE, 'config.yml')


scm_hosts = {
    'hg.mozilla.org': 'hg',
    'git.mozilla.org': 'git',
    'github.com': 'git',
}


def cleanup_url(url):
    git_re = re.compile('\.git$')
    wildcard_re = re.compile('/\*$')
    if git_re.search(url):
        url = url[:-4]
    elif wildcard_re.search(url):
        url = url[:-1]
    return url


def envget(dict, key):
    try:
        return os.environ['DXR_' + key.upper()]
    except KeyError:
        return dict[key]


if __name__ == '__main__':
    if 'VIRTUAL_ENV' not in os.environ:
        activate = os.path.join(HERE, 'venv', 'bin', 'activate_this.py')
        execfile(activate, dict(__file__=activate))
        sys.executable = os.path.join(HERE, 'venv', 'bin', 'python2.7')
        os.environ['VIRTUAL_ENV'] = os.path.join(HERE, 'venv')

    template_env = Environment(
        loader=FileSystemLoader(os.path.join(HERE, 'templates')),
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=False,
    )
    templates = {
        'dxr_config.j2': os.path.join(HERE, 'dxr.config'),
        'jobs.yml.j2': os.path.join(HERE, 'jobs.yml'),
    }

    try:
        f = open(config_file, 'r')
        cfg = yaml.safe_load(f)
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
    finally:
        f.close()

    # override defaults with ENV
    dxr_config = cfg['dxr']
    for i in dxr_config:
        dxr_config[i] = envget(dxr_config, i)

    name_re = re.compile('[/:]')
    trees = []
    for t in cfg['trees']:
        if name_re.search(t['name']) is not None:
            raise Exception("Invalid characters ('/:') in name.", t['name'])
        t['url'] = cleanup_url(t['url'])
        u = urlparse.urlsplit(t['url'])
        if 'subpath' not in t:
            t['subpath'] = u.path.lstrip('/')

        try:
            t['scm'] = scm_hosts[u.netloc]
        except KeyError:
            print 'Unknown host/SCM type'
            raise

        # obj_folder deprecated? bug 842547
        t['object_folder'] = os.path.join('obj', t['subpath'])

        if 'source_folder' not in t:
            t['source_folder'] = os.path.join('src', t['subpath'])

        # merge dicts, with tree dict taking precedence
        trees.append(dict(cfg['defaults'], **t))

    for t in templates:
        with tempfile.NamedTemporaryFile('w',
                                         dir=os.path.dirname(templates[t]),
                                         delete=False) as tf:
            tf.write(template_env.get_template(t).render(trees=trees,
                                                         dxr=dxr_config))
            tempname = tf.name
        os.rename(tempname, templates[t])
