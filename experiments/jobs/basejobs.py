from clusterjobs import job, datafile

class ConfigJob(job.Job):
    """A job with a configuration file"""

    def _finalize(self):
        self.key        = self.jobcfg.key
        self.rep        = self.jobkey.rep
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
