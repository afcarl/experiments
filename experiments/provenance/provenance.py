import os
import time
import subprocess
import collections
import importlib
import platform

import git

import scicfg


pkg_desc = scicfg.SciConfig(strict=True)
pkg_desc._describe('name', instanceof=scicfg.string)
pkg_desc._describe('version', instanceof=scicfg.string)
pkg_desc._describe('commit', instanceof=scicfg.string)
pkg_desc._describe('dirty', instanceof=bool)
pkg_desc._describe('link', instanceof=scicfg.string)


    # PackageInfo

class PkgInfo(object):
    def __init__(self, name, version=None, commit=None, dirty=None, link=None):
        self.name    = name
        self.version = version
        self.commit  = commit
        self.dirty   = dirty
        self.link    = link

    @classmethod
    def from_cfg(cls, pkg_cfg):
        return cls(pkg_cfg.name,
                   version=pkg_cfg._get('version', None),
                   commit=pkg_cfg._get('commit', None),
                   dirty=pkg_cfg._get('dirty', None),
                   link=pkg_cfg._get('link', None))

    def __key(self):
        return (self.name, self.version, self.commit, self.dirty, self.link)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def cfg(self):
        # pkg = importlib.import_module(self.name) # we don't catch the exceptions by design
        pkg_cfg = pkg_desc._deepcopy()
        pkg_cfg.name    = self.name
        if self.version is not None:
            pkg_cfg.version = self.version
        if self.commit is not None:
            pkg_cfg.commit  = self.commit
        if self.dirty is not None:
            pkg_cfg.dirty   = self.dirty
        if self.commit is not None:
            pkg_cfg.link    = self.link
        return pkg_cfg

    def __lt__(self, other):
        return self.name < other.name

    def desc(self):
        if self.commit is not None:
            s = '[{}]'.format(self.commit)
            if self.dirty is True:
                s+= ' (dirty)'
        else:
            assert self.version is not None
            s = self.version
        return s


def py_package_info(pkg_name, link=None):
    """Return the version, and if possible commit and dirtiness of a python package"""
    pkg = importlib.import_module(pkg_name) # we don't catch the exceptions by design

    version = pkg.__version__ # __version__ is *required*
    # commit
    try:
        commit = pkg.__commit__
    except AttributeError:
        commit = None
    # dirty
    try:
        dirty = pkg.__dirty__
    except AttributeError:
        dirty = None
    # link
    if link is None:
        try:
            link = pkg.__url__
        except AttributeError:
            pass

    return PkgInfo(pkg_name, version=version, commit=commit,
                             dirty=dirty, link=link)


    # Platform

plat_desc = scicfg.SciConfig(strict=True)
plat_desc._describe('uname', instanceof=collections.Iterable)
plat_desc._branch('python')
plat_desc._describe('python.compiler', instanceof=str)
plat_desc._describe('python.implementation', instanceof=str)
plat_desc._describe('python.build', instanceof=collections.Iterable)
plat_desc._describe('python.version', instanceof=str)

def platform_info():
    cfg = plat_desc._deepcopy()
    cfg.uname = platform.uname()
    cfg.python.compiler       = platform.python_compiler()
    cfg.python.implementation = platform.python_implementation()
    cfg.python.build          = platform.python_build()
    cfg.python.version        = platform.python_version()

    return cfg


    # Git

def git_commit(working_dir):
    """Return the SHA1 of the current commit"""
    repo = git.Repo(working_dir)
    return repo.head.commit.hexsha

def git_dirty(working_dir):
    """Return True if dirty"""
    repo = git.Repo(working_dir)
    return repo.is_dirty()



    # Provenance

pkg_desc_cfg = scicfg.SciConfig(strict=True)
pkg_desc_cfg._describe('name', instanceof=scicfg.string)
pkg_desc_cfg._describe('desc', instanceof=scicfg.string)
pkg_desc_cfg._describe('link', instanceof=scicfg.string)
pkg_desc_cfg._describe('version_cmd', instanceof=scicfg.string)
pkg_desc_cfg._describe('python', instanceof=bool)


class PkgDesc(object):
    """Describe a package"""

    def __init__(self, name, desc=None, link=None, version_cmd=None, python=True):
        self.name = name
        self.desc = desc
        self.link = link
        self.version_cmd = version_cmd
        self.python = python

    def cfg(self):
        cfg_ = pkg_desc_cfg._deepcopy()
        cfg_.name = self.name
        cfg_.python = self.python
        if self.desc is not None:
            cfg_.desc = self.desc
        if self.link is not None:
            cfg_.link = self.link
        if self.version_cmd is not None:
            cfg_.version_cmd = self.version_cmd
        return cfg_

    @classmethod
    def from_cfg(cls, cfg_desc):
        return cls(cfg_desc.name,
                   cfg_desc._get('desc', None),
                   cfg_desc._get('link', None),
                   cfg_desc._get('version_cmd', None),
                   cfg_desc._get('python', None))


class ProvenanceData(object):
    """An object that generates, holds and checks provenance data"""


    def __init__(self, name, code_dir,
                 research_pkgs=(), thirdparty_py=(), thirdparty=(),
                 timestamp=None, platform=None, env=None, populate=True):
        self.timestamp = timestamp
        if self.timestamp is None:
            self.timestamp = time.time()
        self.platform = platform
        if platform is None:
            self.platform = platform_info()
        self.env_info = None
        if env is not None:
            self.env_info = env.info()

        self.pkgs = {}
        self.dirty_pkgs = []

        self._code_desc = (name, code_dir)
        self._research_pkgs_desc = research_pkgs
        self._thirdparty_py_desc = thirdparty_py
        self._thirdparty_desc    = thirdparty

        self._code          = None
        self._research_pkgs = []
        self._thirdparty_py = []
        self._thirdparty    = []

        if populate:
            self.populate()

    def populate(self):
        self.register_code(*self._code_desc)
        for pkg in self._research_pkgs_desc:
            if isinstance(pkg, scicfg.string):
                pkg = PkgDesc(pkg)
            self.register_py_package(pkg, research=True)

        for pkg in self._thirdparty_py_desc:
            if isinstance(pkg, scicfg.string):
                pkg = PkgDesc(pkg)
            self.register_py_package(pkg, research=False)

        for pkg in self._thirdparty_desc:
            self.register_thirdparty(pkg)

    @property
    def dirty(self):
        return len(self.dirty_pkgs) > 0

    def check_dirty(self):
        if self.dirty:
            raise ValueError("the following packages have dirty gits:"
                             " {}. Won't proceed.".format(self.dirty_pkgs))

    def register_code(self, name, code_dir):
        assert os.path.isdir(code_dir)
        commit = git_commit(code_dir)
        dirty  = git_dirty(code_dir)
        if dirty:
            self.dirty_pkgs.append(name)
        self._code = (name, code_dir, commit, dirty)


    def register_py_package(self, pkg_desc, research=False):
        pkg_info = py_package_info(pkg_desc.name, link=pkg_desc.link)
        self.pkgs[pkg_desc.name] = pkg_info

        if pkg_info.dirty:
            self.dirty_pkgs.append(pkg_desc.name)

        if research:
            self._research_pkgs.append(pkg_info)
            self._research_pkgs.sort()
        else:
            self._thirdparty_py.append(pkg_info)
            self._thirdparty_py.sort()


    def register_thirdparty(self, pkg_desc):
        assert not pkg_desc.python
        if pkg_desc.version_cmd is not None:
            p = subprocess.Popen(pkg_desc.version_cmd.split(), stdout=subprocess.PIPE)
            stdout, stderr = p.communicate()
            version = stdout.decode('utf8').replace('\n', '')
        else:
            version = pkg_desc.desc
        pkg_info = PkgInfo(pkg_desc.name, version=version, link=pkg_desc.link)
        self.pkgs[pkg_desc.name] = pkg_info
        self._thirdparty.append(pkg_info)
        self._thirdparty.sort()


    def message(self):
        s = ''

        # code text
        code_name, code_dir, code_commit, code_dirty = self._code
        if not self.dirty:
            s += ('All the code involved in the execution of this notebook is commited '
                  '(no git repository in dirty state).\n')
        else:
            s += ('Some code involved in the computation has not been commited.\n'
                  'The following repository are in dirty state: {}.\n'.format(
                  ', '.join([name for name in self.dirty_pkgs])))
            s += '\n'

        s += 'This notebook was executed with commit {}{}.\n\n'.format(
             code_commit, ' (dirty)' if code_dirty else '')

        # research package text
        s += 'Installed research packages (available in the submodules/ directory):\n'
        max_name = max(len(pkg.name) for pkg in self._research_pkgs)
        for pkg in self._research_pkgs:
            s += '    {}{} {}\n'.format(pkg.name, ' '*(max_name - len(pkg.name)), pkg.desc())
        s += '\n'

        # third-party python packages
        s += 'Installed third-party python packages:\n'
        for pkg in self._thirdparty_py:
            s += '    {} {}\n'.format(pkg.name, pkg.desc())
        s += '\n'

        # non-python third-party packages
        s += 'Installed third-party non-python packages:\n'
        for pkg in self._thirdparty:
            s += '    {} {}\n'.format(pkg.name, pkg.desc())
        s += '\n'

        # platform info
        s += 'Executed with:\n'
        s += '    {} {} {}\n'.format(self.platform.python.implementation,
                                     self.platform.python.version,
                                     self.platform.python.build)
        s += '    [{}]\n'.format(self.platform.python.compiler)
        s += '    on {}\n'.format(self.platform.uname[3])

        return s


    def cfg(self):
        cfg_ = scicfg.SciConfig(strict=False)
        cfg_._branch('code')
        cfg_.code.name   = self._code[0]
        cfg_.code.commit = self._code[2]
        cfg_.code.dirty  = self._code[3]

        cfg_._branch('research_pkgs')
        for pkg in self._research_pkgs:
            cfg_['research_pkgs'][pkg.name] = pkg.cfg()

        cfg_._branch('thirdparty_py')
        for pkg in self._thirdparty_py:
            cfg_['thirdparty_py'][pkg.name] = pkg.cfg()

        cfg_._branch('thirdparty')
        for pkg in self._thirdparty:
            cfg_['thirdparty'][pkg.name] = pkg.cfg()

        cfg_['platform'] = self.platform
        if self.env_info is not None:
            cfg_['env_info'] = self.env_info

        return cfg_


    def desc(self):
        cfg_desc = scicfg.SciConfig(strict=False)
        cfg_desc._branch('code')
        code_name, code_dir = self._code_desc
        cfg_desc.code.name      = code_name
        cfg_desc.code.directory = code_dir

        cfg_desc._branch('research_pkgs')
        for pkg in self._research_pkgs_desc:
            if isinstance(pkg, scicfg.string):
                pkg = PkgDesc(pkg)
            cfg_desc['research_pkgs'][pkg.name] = pkg.cfg()

        cfg_desc._branch('thirdparty_py')
        for pkg in self._thirdparty_py_desc:
            if isinstance(pkg, scicfg.string):
                pkg = PkgDesc(pkg)
            cfg_desc['thirdparty_py'][pkg.name] = pkg.cfg()

        cfg_desc._branch('thirdparty')
        for pkg in self._thirdparty_desc:
            cfg_desc['thirdparty'][pkg.name] = pkg.cfg()

        return cfg_desc

    @classmethod
    def from_desc(cls, cfg_desc, env=None):
        research_pkgs = [PkgDesc.from_cfg(pkg_desc)
                         for _, pkg_desc in cfg_desc.research_pkgs._branches]
        thirdparty_py = [PkgDesc.from_cfg(pkg_desc)
                         for _, pkg_desc in cfg_desc.thirdparty_py._branches]
        thirdparty    = [PkgDesc.from_cfg(pkg_desc)
                         for _, pkg_desc in cfg_desc.thirdparty._branches]
        return cls(cfg_desc.code.name, cfg_desc.code.directory,
                   research_pkgs, thirdparty_py, thirdparty, env=env)

    def same_cfg(self, other_cfg):
        this_cfg = self.cfg()
        check = True
        check = check and this_cfg.research_pkgs == other_cfg.research_pkgs
        check = check and this_cfg.thirdparty_py == other_cfg.thirdparty_py
        check = check and this_cfg.thirdparty    == other_cfg.thirdparty

        check = check and this_cfg.platform.python == other_cfg.platform.python
        check = check and this_cfg._get('env_info', None) == other_cfg._get('env_info', None)
        return check


class ProvenanceAccumulator(object):

    def __init__(self, code_dir=None):
        self._current_commit = None
        self._current_dirty  = None
        if code_dir is not None:
            self.register_code(code_dir)

        self._code = set()
        self._research_pkgs = {}
        self._thirdparty_py = {}
        self._thirdparty    = {}
        self._pythons       = set()

        self.dirty_pkgs = set()

    def __key(self):
        return (self._code, self._research_pkgs, self._thirdparty_py,
                self._thirdparty_py, self.dirty_pkgs)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def register_code(self, code_dir):
        assert os.path.isdir(code_dir)
        self._current_commit = git_commit(code_dir)
        self._current_dirty  = git_dirty(code_dir)

    def tracks(self):
        n = 0
        n = max(n, len(self._code))
        n = max(n, max(len(pkgs) for pkgs in self._research_pkgs.values()))
        n = max(n, max(len(pkgs) for pkgs in self._thirdparty_py.values()))
        n = max(n, max(len(pkgs) for pkgs in self._thirdparty.values()))
        n = max(n, len(self._pythons))
        return n

    def add_cfg(self, cfg):
        code = (cfg.code.name, cfg.code.commit, cfg.code.dirty)
        self._code.add(code)
        if cfg.code.dirty:
            self.dirty_pkgs.add(cfg.code.name)

        for pkg_name, pkg_cfg in cfg.research_pkgs._branches:
            self._research_pkgs.setdefault(pkg_name, set())
            pkg_info = PkgInfo.from_cfg(pkg_cfg)
            if pkg_info.dirty:
                self.dirty_pkgs.add(pkg_name)
            self._research_pkgs[pkg_name].add(pkg_info)

        for pkg_name, pkg_cfg in cfg.thirdparty_py._branches:
            self._thirdparty_py.setdefault(pkg_name, set())
            pkg_info = PkgInfo.from_cfg(pkg_cfg)
            if pkg_info.dirty:
                self.dirty_pkgs.add(pkg_name)
            self._thirdparty_py[pkg_name].add(pkg_info)

        for pkg_name, pkg_cfg in cfg.thirdparty._branches:
            self._thirdparty.setdefault(pkg_name, set())
            pkg_info = PkgInfo.from_cfg(pkg_cfg)
            if pkg_info.dirty:
                self.dirty_pkgs.add(pkg_name)
            self._thirdparty[pkg_name].add(pkg_info)

        self._pythons.add((cfg.platform.python.implementation,
                           cfg.platform.python.version,
                           cfg.platform.python.build,
                           cfg.platform.python.compiler))

    def message(self):
        s = ''

        # code text
        if len(self.dirty_pkgs) == 0:
            s += ('All the code involved in the cluster computation was commited during job execution.\n')
        else:
            s += ('Some code involved in the cluster computation was not commited.\n'
                  'The following repository are in dirty state: {}.\n'.format(
                  ', '.join([name for name in self.dirty_pkgs])))
        if self.tracks() == 1:
            s += ('Every job was run with the same code version.\n')
        else:
            s += ('At least {} different versions of the code were used to compute the cluster jobs.\n'.format(self.tracks()) +
                  'No job was computed with more than one version.\n')
        s += '\n'

        s += 'The cluster jobs were launched with commit{}: '.format('s' if len(self._code) > 1 else '')
        s += ', '.join('{}{}'.format(code_commit, ' (dirty)' if code_dirty else '')
                       for code_name, code_commit, code_dirty in self._code)
        s += '.\n\n'

        # research package text
        s += 'Installed research packages during cluster jobs execution:\n'
        max_name = max(len(pkg_name) for pkg_name in self._research_pkgs.keys())
        for pkg_name, pkgs in self._research_pkgs.items():
            s += '    {}{} '.format(pkg_name, ' '*(max_name - len(pkg_name)))
            s += ', '.join(pkg.desc() for pkg in pkgs)
            s += '\n'
        s += '\n'

        # third-party python packages
        s += 'Installed third-party python packages during cluster jobs execution:\n'
        for pkg_name, pkgs in self._thirdparty_py.items():
            s += '    {} '.format(pkg_name)
            s += ', '.join(pkg.desc() for pkg in pkgs)
            s += '\n'
        s += '\n'

        # non-python third-party packages
        s += 'Installed third-party non-python packages during cluster jobs execution:\n'
        for pkg_name, pkgs in self._thirdparty.items():
            s += '    {} '.format(pkg_name)
            s += ', '.join(pkg.desc() for pkg in pkgs)
            s += '\n'
        s += '\n'

        # # platform info
        assert len(self._pythons) == 1
        implementation, version, build, compiler = list(self._pythons)[0]
        s += 'Cluster jobs were executed with:\n'
        s += '    {} {} {}\n'.format(implementation, version, build)
        s += '    [{}]\n'.format(compiler)
        s += '\n'

        s += 'This notebook was executed with code commit: {}{}.\n'.format(
             self._current_commit, ' (dirty)' if self._current_dirty else '')

        return s
