#!/usr/bin/env python
# encoding: utf-8
"""
logger.py

Created by Paul Fudal on 2014-04-2.
Copyright (c) 2014 INRIA. All rights reserved.
"""
import time
import os
import atexit
import threading
from threading import Thread

from clusterjobs import datafile


class ChronoHistory(object):

    def __init__(self, core_filepath, extra_filepath=None, autosave_period=60, folder='',
                 core_keys=('exploration', 'feedback'), extralog=False, load=True,
                 verbose=False, meta=None):

        self.core_keys = core_keys
        self.extralog = extralog

        self.core  = ChronoLog(core_filepath, folder=folder,
                               autosave_period=autosave_period, load=load, verbose=verbose, meta=meta)
        if self.extralog:
            assert extra_filepath is not None
            self.extra = ChronoLog(core_filepath + '.logs', folder=folder,
                                   autosave_period=autosave_period, load=load, verbose=verbose, meta=meta)

    @property
    def meta(self):
        return self.core.meta

    @meta.setter
    def meta(self, val):
        self.core.meta = val
        if self.extralog:
            self.extra.meta = val

    def _core_data(self, data):
        return {k: data[k] for k in self.core_keys}

    def add_entry(self, t, data, delete_posterior=True):
        core_data = self._core_data(data)
        self.core.add_entry(t, core_data, delete_posterior=delete_posterior)
        if self.extralog:
            self.extra.add_entry(t, data, delete_posterior=delete_posterior)

    def setdefault(self, t, data):
        core_data = self._core_data(data)
        self.core.setdefault(t, core_data)
        if self.extralog:
            self.extra.setdefault(t, data)

    def load(self, verbose=False):
        self.core.load(verbose=verbose)
        if self.extralog:
            self.extra.load(verbose=verbose)

    def save(self, done=False, verbose=False):
        self.core.save(verbose=verbose)
        if self.extralog:
            self.extra.save(verbose=verbose)
        if done:
            self.core.done(verbose=verbose)

    def enable_autosave(self):
        self.core.enable_autosave()
        if self.extralog:
            self.extra.enable_autosave()

    def disable_autosave(self):
        self.core.disable_autosave()
        if self.extralog:
            self.extra.disable_autosave()

    def close(self):
        self.core.close()
        if self.extralog:
            self.extra.close()

    def __iter__(self):
        """Iter over keys."""
        if self.extralog:
            for entry in self.extra:
                yield entry
        else:
            for entry in self.core:
                yield entry

    def __len__(self):
        return len(self.core.entries)

class ChronoLog(object):
    """This describe a logger system able to write data in a file"""

    def __init__(self, filename, folder='', meta=None, autosave_period=60, load=True, verbose=False):
        """"""
        self.filename = filename
        self.folder = datafile.normpath(folder)
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        self.meta = meta

        self.autosave_period = autosave_period
        self.verbose = verbose

        self.lock = threading.Lock()

        self.entries = []

        self.autosave = False
        self.autowriter = None

        self.closed = False
        atexit.register(self.close)

        if load:
            self.load(self.verbose)

    @staticmethod
    def writer_function(logger):
        """Function call by the deamon thread"""
        while logger.autosave:
            start_wait = time.time()
            while time.time() - start_wait < logger.autosave_period:
                if not logger.autosave:
                    break
                time.sleep(0.5)

            if logger.autosave:
                logger.save()

    def enable_autosave(self):
        self.autosave = True
        self.autowriter = Thread(target=self.writer_function, args={self,})
        self.autowriter.daemon = True
        self.autowriter.start()

    def disable_autosave(self):
        self.autosave = False

    def setdefault(self, t, data):
        self.lock.acquire()
        self.entries.extend([None]*max(0, (t+1)-len(self.entries)))
        if self.entries[t] is None:
            self.entries[t] = {'t'        : t,
                               'timestamp': time.time(),
                               'data'     : data}
        self.lock.release()


    def add_entry(self, t, data, delete_posterior=True):
        """"""
        self.lock.acquire()
        self.entries.extend([None]*max(0, (t+1)-len(self.entries)))
        if delete_posterior:
            self.entries = self.entries[:t+1]

        self.entries[t] = {'t'        : t,
                           'timestamp': time.time(),
                           'data'     : data}
        self.lock.release()

    def load(self, verbose=False):
        filepath = os.path.join(self.folder, self.filename)
        self.lock.acquire()
        try:
            if os.path.isfile(filepath) or os.path.isfile(filepath+'.bz2'):
                data = datafile.load_file(filepath,
                                          typename='data',
                                          verbose=verbose)
                self.entries = data['entries']
                self.meta    = data['meta']
            else:
                if verbose:
                    print('warning: could not find {}'.format(filepath))
                self.entries = []
        finally:
            self.lock.release()

    def save(self, verbose=False):
        filepath = os.path.join(self.folder, self.filename)
        self.lock.acquire()
        try:
            datafile.save_file({'entries': self.entries, 'meta': self.meta},
                               filepath,
                               typename='data', verbose=verbose)
        finally:
            self.lock.release()

    def delete(self):
        self.lock.acquire()
        try:
            datafile.delete_file(self.filename, directory=self.folder, typename='data')
        finally:
            self.lock.release()

    def close(self):
        if not self.closed:
            if self.autosave:
                self.disable_autosave()
                self.save()
            self.closed = True

    def done(self, verbose=False):
        """Write a empty file to show the experiment is over"""
        filepath = os.path.join(self.folder, self.filename)
        datafile.save_text('', filepath+'.done', verbose=verbose)


    def __iter__(self):
        for entry in self.entries:
            yield entry
