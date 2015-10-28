import os
from distutils.core import setup

setup(
    name = "experiments",
    version = "1.0",
    author = "Fabien Benureau",
    author_email = "fabien.benureau@gmail.com",
    description = ("Library to run cluster (and non-cluster) experiments for articles"),
    license = "Open Science License",
    keywords = "clusters science",
    url = "github.com/humm/experiments.git",
    packages=['experiments',
              'experiments.data',
              'experiments.jobs',
              'experiments.runs',
              'experiments.tools'],
    #long_description=read('README'),
    classifiers=[],
    requires=['clusterjobs', 'forest', 'explorers', 'environments', 'learners']
)
