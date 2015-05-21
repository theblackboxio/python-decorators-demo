__author__ = 'guillermoblascojimenez'

import decorators

@decorators.logging
@decorators.not_null
@decorators.precondition(lambda x: x >= 0)
@decorators.Hint(recursion=True)
@decorators.Cache()
def fibonacci(x):
    if x == 0 or x == 1:
        return 1
    else:
        return fibonacci(x-1) + fibonacci(x-2)


@decorators.not_null
@decorators.precondition(lambda x: x >= 0)
def n_fibonacci(n):
    @decorators.logging
    @decorators.not_null
    @decorators.precondition(lambda x: x >= 0)
    @decorators.Hint(recursion=True)
    @decorators.Cache()
    def fibonacci(x):
        if x == 0 or x == 1:
            return 1
        else:
            return sum((fibonacci(x - i) for i in xrange(1, n + 1) if x - i >= 0))
    return fibonacci


if __name__ == '__main__':
    print fibonacci(50)