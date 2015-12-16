import collections
import platform
import importlib

import git

import scicfg


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


pkg_desc = scicfg.SciConfig(strict=True)
pkg_desc._describe('version', instanceof=(str, unicode))
pkg_desc._describe('commit', instanceof=(str, unicode))
pkg_desc._describe('dirty', instanceof=bool)

def packages_info(package_names):
    cfg = scicfg.SciConfig(strict=False)
    for pkg_name in package_names:
        pkg = importlib.import_module(pkg_name) # we don't catch the exceptions by design
        pkg_cfg = pkg_desc._deepcopy()
        pkg_cfg.version = pkg.__version__ # __version__ is *required*
        try:
            pkg_cfg.commit = pkg.__commit__
        except AttributeError:
            pass
        try:
            pkg_cfg.dirty = pkg.__dirty__
        except AttributeError:
            pass
        cfg[pkg_name] = pkg_cfg

    return cfg

def check_dirty(provenance_cfg, force=False):
    if force or provenance_cfg.check_dirty:
        dirty_pkgs = []
        for pkg_name, cfg in provenance_cfg.packages._branches:
            try:
                if cfg.dirty:
                    dirty_pkgs.append(pkg_name)
            except KeyError:
                pass
        for code_name, cfg in provenance_cfg.code._branches:
            if cfg.dirty:
                dirty_pkgs.append(code_name)

        if len(dirty_pkgs) > 0:
            raise ValueError("the following packages have dirty gits: {}. Won't proceed.".format(dirty_pkgs))

def git_commit(working_dir):
    """Return the SHA1 of the current commit"""
    repo = git.Repo(working_dir)
    return repo.head.commit.hexsha

def git_dirty(working_dir):
    """Return True if dirty"""
    repo = git.Repo(working_dir)
    return repo.is_dirty()

def gather_provenance(cfg, env):
    prov_cfg = scicfg.SciConfig()
    prov_cfg.check_dirty = cfg.provenance.check_dirty
    prov_cfg.packages = packages_info(cfg.provenance.package_names)
    prov_cfg.platform = platform_info()
    prov_cfg.env      = env.info()
    prov_cfg.code     = cfg.provenance._get('code', scicfg.SciConfig())

    if cfg.provenance.check_dirty:
        provenance.check_dirty(prov_cfg)

    return prov_cfg

def check_provenance(cfg, prov_cfg):
    if cfg.provenance.check_continuity:
        assert cfg.provenance.packages        == prov_cfg.packages
        assert cfg.provenance.platform.python == prov_cfg.platform.python
        assert cfg.provenance.env             == prov_cfg.env
