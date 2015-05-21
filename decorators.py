__author__ = 'guillermoblascojimenez'

import collections
import functools
import threading

# Cache decorators


def cache(f):
    '''
    Decorator that for a given deterministic function caches the input/output pairs, so later calls with the same
    input does not rely in function implementation but in a dict lookup.
    '''
    cache_dict = {}

    @functools.wraps(f)
    def wrapper(*x):
        if isinstance(x, collections.Hashable):
            if x in cache_dict:
                return cache_dict[x]
            else:
                v = f(*x)
                cache_dict[x] = v
                return v
        else:
            return f(*x)
    return wrapper


class _CachedItem():

    def __init__(self, value, hits, inserted, accessed):
        self.value = value
        self.hits = hits
        self.inserted = inserted
        self.accessed = accessed

    def __eq__(self, other):
        return other.value == self.value

    def __hash__(self):
        return hash(self.value)


def _reverse_dict(d):
    n = {}
    for k, v in d.iteritems():
        if v not in n:
            n[v] = []
        n[v].append(k)
    return {k: tuple(v) for k, v in n.iteritems()}


class Cache:
    def __init__(self, max_size=5, removal_policy='LEAST_ACCESSED'):
        self.maxSize = max_size
        self.removalPolicy = removal_policy
        assert removal_policy in ('LEAST_INSERTED', 'LEAST_ACCESSED', 'LEAST_HIT',)

    def __call__(self, f):
        functools.wraps(f)
        self.cache = {}
        self.inserted = 0
        self.accessed = 0

        @functools.wraps(f)
        def wrapper(*x):
            if isinstance(x, collections.Hashable):
                if x in self.cache:
                    self.cache[x].accessed = self.accessed
                    self.accessed += 1
                    self.cache[x].hits += 1
                    return self.cache[x].value
                else:
                    v = f(*x)
                    self.cache[x] = _CachedItem(v, 0, self.inserted, self.accessed)
                    self.inserted += 1
                    self.accessed += 1
                    if len(self.cache) > self.maxSize:
                        key_to_remove = []
                        if self.removalPolicy == 'LEAST_INSERTED':
                            ins = _reverse_dict({k: v.inserted for k, v in self.cache.iteritems()})
                            min_ins = min(ins.keys())
                            key_to_remove = ins[min_ins]
                        if self.removalPolicy == 'LEAST_ACCESSED':
                            ins = _reverse_dict({k: v.accessed for k, v in self.cache.iteritems()})
                            min_ins = min(ins.keys())
                            key_to_remove = ins[min_ins]
                        if self.removalPolicy == 'LEAST_HIT':
                            ins = _reverse_dict({k: v.hits for k, v in self.cache.iteritems()})
                            min_ins = min(ins.keys())
                            key_to_remove = ins[min_ins]
                        for k in key_to_remove:
                            del self.cache[k]
                    return v
            else:
                return f(*x)
        return wrapper


# Precondition decorator


def precondition(precond, message='Precondition failed'):
    def wrapper_factory(f):
        @functools.wraps(f)
        def wrapper(*x):
            if not precond(*x):
                raise ValueError(message)
            else:
                return f(*x)
        return wrapper
    return wrapper_factory


class Precondition:

    def __init__(self, precond, message='Precondition failed'):
        self.precond = precond
        self.message = message

    def __call__(self, f):
        @functools.wraps(f)
        def wrapper(*x):
            if not self.precond(*x):
                raise ValueError(self.message)
            else:
                return f(*x)
        return wrapper


def not_null(f):
    return precondition(lambda x: x is not None, 'Null reference exception')(f)


class Retry:

    def __init__(self, condition):
        self.condition = condition

    def __call__(self, f):

        @functools.wraps(f)
        def wrapper(*x):
            repeat = True
            n = 0
            while repeat:
                try:
                    v = f(*x)
                    return v
                except Exception as a:
                    repeat = self.condition(a, n)

        return wrapper


class RetryNTimes(Retry):

    def __init__(self, times=2):
        Retry.__init__(self, lambda (x, n): n < times)


def logging(f):
    @functools.wraps(f)
    def wrapper(*x):
        print "[LOG] {0}({1})".format(f.__name__, *x)
        return f(*x)
    return wrapper


class Hint:

    def __init__(self, recursion=True, max_recursion=5):
        self.recursion = recursion
        self.maxRecursion = max_recursion
        self.currentRecursionPerThread = {}

    def __call__(self, f):

        @functools.wraps(f)
        def wrapper(*x):
            this_thread = threading.current_thread().ident
            if this_thread not in self.currentRecursionPerThread:
                self.currentRecursionPerThread[this_thread] = 0
            self.currentRecursionPerThread[this_thread] += 1
            this_recursion = self.currentRecursionPerThread[this_thread]
            if self.recursion and this_recursion > self.maxRecursion:
                print "[HINT] Too many recursion for {0}, {1} recursion levels of {2} allowed."\
                    .format(f.__name__, this_recursion, self.maxRecursion)
            exception = None
            v = None
            try:
                v = f(*x)
            except Exception as e:
                exception = e
            finally:
                self.currentRecursionPerThread[this_thread] -= 1
                if exception is not None:
                    raise exception
                else:
                    return v
        return wrapper