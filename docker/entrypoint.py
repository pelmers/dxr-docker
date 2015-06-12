#!/usr/bin/env python2.7
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import requests
import subprocess
import sys
import urlparse
import yaml

from jinja2 import Environment, FileSystemLoader
from lxml import etree

dxr_home = os.environ['DXR_HOME']
cfg_dir = dxr_home
config_file = os.path.join(cfg_dir, 'config.yml')
git_re = re.compile(r'git(hub\.com|\.mozilla\.(org|com))')
hg_re = re.compile(r'hg\.mozilla\.org')


class Unbuffered(object):

    # Dirty hack to make stdout unbuffered. This matters for Docker log viewing.

    def __init__(self, s):
        self.s = s

    def write(self, d):
        self.s.write(d)
        self.s.flush()

    def __getattr__(self, a):
        return getattr(self.s, a)

sys.stdout = Unbuffered(sys.stdout)

# We also assign stderr to stdout because Docker sometimes doesn't capture
# stderr by default.
sys.stderr = sys.stdout


class IndexTree(object):

    def __init__(self, tree):
        self.tree = tree
        self.load_config(config_file, self.tree)
        self.template_env = Environment(
            loader=FileSystemLoader(os.path.join(cfg_dir, 'templates')),
            keep_trailing_newline=False,
            lstrip_blocks=False,
            trim_blocks=False,
        )
        self.templates = {
            'mozconfig.j2': os.path.join(self.config['source_dest'],
                                         '.mozconfig'),
        }

    # if url were in dxr.config we could use that instead
    def load_config(self, config, tree):
        try:
            f = open(config, 'r')
            cfg = yaml.safe_load(f)
            self.config = cfg[tree]
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
        except (KeyError, AttributeError):
            print "Missing entry for tree:", tree
        else:
            f.close()
        if 'source_folder' not in self.config:
            self.config['source_folder'] = os.path.join('src',
                                                        self.tree)
        url = urlparse.urlsplit(self.config['url'])
        self.config['netloc'] = url.netloc
        if git_re.match(url.netloc):
            self.cmd = 'git'
            self.update_cmd = ['fetch', '-u']
        elif hg_re.match(url.netloc):
            self.cmd = 'hg'
            self.update_cmd = ['pull', '-u']
        else:
            # TODO: raise error
            print 'No match'

    def render_template(self, template):
        return self.template_env.get_template(template).render(self.config)

    def create_mozconfig(self):
        mozconfig = os.path.join(self.config['source_folder'], '.mozconfig')
        if not self.config['build_command']:
            continue
        elif os.path.exists(mozconfig):
            continue
        else:
            with open(mozconfig, 'a') as f:
                contents = self.render_template('mozconfig.j2')
                f.write(contents)
                f.close()

    def scrape_page(url, xpath):
        page = requests.get(url)
        return etree.HTML(page.content).xpath(xpath)

    def scrape_hgmo(self, url):
        repos = self.scrape_page(url, "//td/a[@class='list']/b/text()")
        return [url + r for r in repos]

    def scrape_gitmo(self, url):
        u = urlparse.urlsplit(url)
        baseurl = "{0}://{1}/".format(u.scheme, u.netloc)
        repos = self.scrape_page(baseurl, "//td/a[@class='list']/text()")
        regex = re.compile('^%s.*' % u.path[1:])
        return [baseurl + r for r in repos if regex.search(r)]

    def scrape_gh(url):
        # must use api.github.com/{users,org}/name/
        url += 'repos'
        req_json = requests.get(url).json()
        return [r["clone_url"] for r in req_json]

    def scrape(self, url):
        host = self.config['netloc']
        if host == 'hg.mozilla.org':
            repos = self.scrape_hgmo(url)
        elif host == 'git.mozilla.org':
            repos = self.scrape_gitmo(url)
        elif host == 'github.com':
            repos = self.scrape_gh(url)
        else:
            # TODO: raise error
            print "error"
        return repos

    def update_src(self):
        url = self.config['url']
        source_dir = self.config['source_folder']
        parent_dir = os.path.dirname(source_dir)
        glob_re = re.compile('/\*$')
        if not os.path.exists(source_dir):
            try:
                os.lstat(parent_dir)
            except OSError:
                os.makedirs(parent_dir, 0755)
            if glob_re.search(url):
                repos = self.scrape(url[:-1])
            else:
                repos = [url]
            for r in repos:
                subprocess.check_call([self.cmd, 'clone', r], cwd=parent_dir)
        else:
            if glob_re.search(url):
                dir_list = os.listdir(source_dir)
                # TODO: clean this up
                dirs = [os.path.join(source_dir, d) for d in dir_list if
                        os.path.isdir(os.path.join(source_dir, d))]
            else:
                dirs = [source_dir]
            for d in dirs:
                subprocess.check_call([self.cmd] + self.update_cmd, cwd=d)


if __name__ == "__main__":
    for name in sys.argv[1:]:
        project = IndexTree(name)
        try:
            project.update_src()
        except subprocess.CalledProcessError as e:
            print "Error: {0} returned {1}".format(e.cmd, e.returncode)
        except:
            print "Something went wrong with {0}!".format(project)
        project.create_mozconfig()
        sys.stdout.flush()
        os.execv('venv/bin/dxr',
                 ['venv/bin/dxr', 'index', '-v', '--config', 'dxr.config'])
