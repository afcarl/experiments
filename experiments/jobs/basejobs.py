from clusterjobs import job, datafile

from .keys import JobKey, expkey


class ConfigJob(job.Job):
    """A job with a configuration file"""

    def _finalize(self):
        self.key        = self.jobcfg.key
        self.rep        = self.jobkey.rep
        self._name      = self.jobcfg.name
        if self.jobgroup is not None:
            self.jobgroup.add_job(self)

    def prepare_hd(self):
        datafile.save_config(self.jobcfg, filename=self.jobcfg.hardware.configfile,
                                          directory=self.context.fulldir)

    def qsub_options(self):
        if 'qsub.resources' in self.jobcfg:
            options = ['{}={}'.format(key, value) for key, value in self.jobcfg.qsub.resources._items()]
            if len(options) > 0:
                return '-l {}'.format(','.join(sorted(options)))
        return ''

    def command(self):
        if self.context.qsub:
            cmd = 'qsub {} -v configfile={} -N {} -d {} {};'.format(
                self.jobkey.foldername + '/run.pbs',
                self.jobcfg.hardware.configfile,
                self.name, self.context.fulldir, self.qsub_options())
        else:
            cmd = 'cd {}; time python -c "import experiments; experiments.run_job()" {}'.format(
                self.context.fulldir, self.jobcfg.hardware.configfile)
        return cmd


class SetupJob(job.Job):
    """A job to create the main directory and copy the pbs script"""

    def prepare(self, args):
        self.expcfg, self.pbs_script = args
        self.jobkey = JobKey(('setup',), expkey(self.expcfg), 0)


        self.key        = self.jobkey.key
        self.rep        = self.jobkey.rep
        self._name = '{}/run.pbs'.format(self.jobkey.foldername)
        self.add_output_file(self._name, full=True)

        if self.jobgroup is not None:
            self.jobgroup.add_job(self)

    def prepare_hd(self):
        datafile.save_text(self.pbs_script, self.name, directory=self.context.fulldir, verbose=True)

    def command(self):
        return ''
