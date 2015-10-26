import os, sys, stat
import argparse
import subprocess

from . import jobs

def parser():
    p = argparse.ArgumentParser(description='configure jobs for experiments')
    p.add_argument('--hd', dest='hd',    default=False, action='store_true', help='write config files to disk')
    p.add_argument('--noqsub', dest='noqsub',    default=False, action='store_true', help='act as if qsub was not available')
    p.add_argument('-v', dest='verbose', default=False, action='store_true', help='display job status')
    p.add_argument('-w', dest='werbose', default=False, action='store_true', help='display job status, without done jobs')
    p.add_argument('-a', dest='analysis', default=False, action='store_true', help='run analysis jobs')
    p.add_argument('-q', dest='quiet',   default=False, action='store_true', help='display only task counts. override verbose and werbose')
    p.add_argument('-t', dest='tmp_res', default=False, action='store_true', help='compute temporary results')
    p.add_argument('-r', dest='result_only', default=False, action='store_true', help='compute only results')
    p.add_argument('--run', dest='run',  default=False, action='store_true', help='launch the necessary commands from python')
    return p.parse_args()

def grp_cmdline(grp, script_name='run.sh', rep_modulo=(1, 0)):
    args = parser()

    if args.noqsub:
        for job in grp.jobs:
            job.context.qsub = False
    if args.hd:
        grp.prepare_hds()
    grp.update_group()

    job_subset = set()
    for job in grp.jobs:
        if (not hasattr(job, 'key')) or job.rep % rep_modulo[0] == rep_modulo[1]:
            job_subset.add(job.name)

    job_torun = set(job.name for job in grp.to_run())
    job_torun = job_torun.intersection(job_subset)

    if args.verbose or args.werbose:
        grp.print_status(done=not args.werbose, quiet=args.quiet, job_subset=job_subset)

    if args.run:
        cmds = grp.run_commands(job_names=job_torun)
        for cmd in cmds:
            subprocess.call(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, shell=True)


from clusterjobs import context, jobgroup

def populate_grp(cfg, grp):
    ctx = context.Context(cfg.meta.rootpath, cfg.exp.path)

    ex_jobs = []
    for rep in range(cfg.exp.repetitions):
        ex_jobs.append(jobs.ExplorationJob(ctx, (), (cfg, rep), jobgroup=grp))

    for testsetname in cfg.testsets._children_keys():
        jobs.TestsetJob(ctx, (), (cfg, testsetname), jobgroup=grp)

    for testname in cfg.tests._children_keys():
        for ex_job in ex_jobs:
            jobs.TestJob(ctx, (), (cfg, ex_job, testname), jobgroup=grp)

        jobs.ResultJob(ctx, (), (cfg, testname), jobgroup=grp)


def run_exps(cfgs):
    grp = jobgroup.JobBatch(context.Env(user=cfgs[0].meta.user))

    for cfg in cfgs:
        populate_grp(cfg, grp)

    grp_cmdline(grp)
