from clusterjobs import job, datafile


class JobKey(object):
    """Handles naming things in unique ways"""

    def __init__(self, kind, exp_key, rep):
        self.kind = tuple(kind)
        self.exp_name = exp_key[0]
        self.deps     = exp_key[1]
        self.rep      = rep

    @property
    def key(self):
        return (tuple(self.kind), tuple(self.exp_name), tuple(self.deps), self.rep)

    @property
    def name(self):
        s = '[{}]'.format(']['.join(self.exp_name))
        return '{}.{:02d}'.format(s, self.rep)

    @property
    def filepath(self):
        s = '[{}]'.format(']['.join(self.exp_name))
        return '{}/{}'.format(s, self.name)

def expkey(cfg):
    return (tuple(cfg.exp.prefix) + (cfg.exploration.ex_name, cfg.exploration.env_name), cfg.exploration.deps, cfg.exp.repetitions)

class ConfigJob(job.Job):
    """A job with a configuration file"""

    def _finalize(self):
        self.key        = self.jobcfg.key
        self._name      = self.jobcfg.name
        self.jobgroup.add_job(self)

    def prepare_hd(self):
        datafile.save_config(self.jobcfg, filename=self.jobcfg.hardware.configfile,
                                          directory=self.context.fulldir)
    def command(self):
        if self.context.qsub:
            assert False
            cmd = 'qsub {} -v cmd={},configfile={} -N {} -d {} {};'.format(
                self.context.fullpath('{}.pbs'.format(filenames.foldername(('setup',) + self.cfg.exp.key))), self.cmd,
                self.context.rootpath(self.cfg[self.cfg.job.key[0]].hardware.configfile),
                self.name, self.context.rootdir, self.qsub_options())
        else:
            cmd = 'cd {}; time python -c "import experiments; experiments.run_job()" {}'.format(
                self.context.fulldir, self.jobcfg.hardware.configfile)
        return cmd
