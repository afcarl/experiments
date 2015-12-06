from setuptools import setup

import versioneer

VERSION = '1.0'

setup(
    name         = "experiments",
    version      = VERSION,
    cmdclass     = versioneer.get_cmdclass(),
    author       = "Fabien Benureau",
    author_email = "fabien.benureau@gmail.com",
    description  = "Library to run cluster (and non-cluster) experiments for articles",
    license      = "Open Science License",
    keywords     = "clusters science",
    url          = "https://github.com/humm/experiments.git",
    packages=['experiments',
              'experiments.data',
              'experiments.jobs',
              'experiments.provenance',
              'experiments.runs',
              'experiments.tools'],
    #long_description=read('README'),
    classifiers=[],
    install_requires=['clusterjobs', 'scicfg', 'explorers', 'environments', 'learners', 'gitpython'],

    # in order to avoid 'zipimport.ZipImportError: bad local file header'
    zip_safe=False,
)
