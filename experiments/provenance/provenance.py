import collections
import platform
import importlib

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


mod_desc = scicfg.SciConfig(strict=True)
mod_desc._describe('version', instanceof=(str, unicode))
mod_desc._describe('commit', instanceof=(str, unicode))
mod_desc._describe('dirty', instanceof=bool)

def modules_provenance(module_names):
    cfg = scicfg.SciConfig(strict=False)
    for mod_name in module_names:
        mod = importlib.import_module(mod_name) # we don't catch the exceptions by design
        mod_cfg = mod_desc._deepcopy()
        mod_cfg.version = mod.__version__ # __version__ is *required*
        try:
            mod_cfg.commit = mod.__commit__
        except AttributeError:
            pass
        try:
            mod_cfg.dirty = mod.__dirty__
        except AttributeError:
            pass
        cfg[mod_name] = mod_cfg

    return cfg

def check_dirty(module_cfg):
    dirty_mods = []
    for mod_name, cfg in module_cfg._branches:
        try:
            if cfg.dirty:
                dirty_mods.append(mod_name)
        except KeyError:
            pass
    if len(dirty_mods) > 0:
        raise ValueError("the following modules are dirty: {}. Won't proceed.".format(dirty_mods))

if __name__ == '__main__':
    print(modules(['explorers', 'learners', 'environments']))
    print(platform_info())
