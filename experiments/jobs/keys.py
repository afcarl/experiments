"""
Here we deal with providing different jobs with different keys.
"""

EXTS = {'exploration': 'd',
        'testset'    : 'ts',
       }


"""
kinone.ts.d
[reuse][ball0][random.motor].d
[reuse][ball0][random.motor].tcov.d
[reuse][ball0][random.motor].tcov.r.d
"""

def kind2ext(kind):
    if kind[0] == 'exploration':
        return ''
    elif kind[0] == 'testset':
        return '.ts'
    elif kind[0] == 'test':
        assert len(kind) >= 2, '{} is not at least of lenght 2'.format(kind)
        return '.{}'.format(kind[1])
    elif kind[0] == 'result':
        assert len(kind) >= 2, '{} is not at least of lenght 2'.format(kind)
        return '.{}.r'.format(kind[1])


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
        return '{}.{:02d}{}'.format(s, self.rep, kind2ext(self.kind))

    @property
    def foldername(self):
        return  '[{}]'.format(']['.join(self.exp_name))

    @property
    def filepath(self):
        return '{}/{}'.format(self.foldername, self.name)

def expkey(cfg):
    return (tuple(cfg.exp.prefix) + (cfg.exploration.ex_name, cfg.exploration.env_name), cfg.exploration.deps, cfg.exp.repetitions)
