"""Generic re-useable self-contained helper functions."""

import functools
import inspect
import itertools
import logging
import os
import typing
import warnings

__all__ = ['SKIP_DEPRECATION',
           'attach',
           'mkdirs',
           'mapping_items',
           'deprecate_positional_args']

SKIP_DEPRECATION = object()


log = logging.getLogger(__name__)


def attach(object: typing.Any, name: str) -> typing.Callable:
    """Return a decorator doing ``setattr(object, name)`` with its argument.

    >>> spam = type('Spam', (object,), {})()  # doctest: +NO_EXE

    >>> @attach(spam, 'eggs')
    ... def func():
    ...     pass

    >>> spam.eggs  # doctest: +ELLIPSIS
    <function func at 0x...>
    """
    def decorator(func):
        setattr(object, name, func)
        return func

    return decorator


def mkdirs(filename, *, mode: int = 0o777) -> None:
    """Recursively create directories up to the path of ``filename``
        as needed."""
    dirname = os.path.dirname(filename)
    if not dirname:
        return
    log.debug('os.makedirs(%r)', dirname)
    os.makedirs(dirname, mode=mode, exist_ok=True)


def mapping_items(mapping):
    """Return an iterator over the ``mapping`` items,
        sort if it's a plain dict.

    >>> list(mapping_items({'spam': 0, 'ham': 1, 'eggs': 2}))  # doctest: +NO_EXE
    [('eggs', 2), ('ham', 1), ('spam', 0)]

    >>> from collections import OrderedDict
    >>> list(mapping_items(OrderedDict(enumerate(['spam', 'ham', 'eggs']))))
    [(0, 'spam'), (1, 'ham'), (2, 'eggs')]
    """
    result = iter(mapping.items())
    if type(mapping) is dict:
        result = iter(sorted(result))
    return result


def deprecate_positional_args(*,
                              supported_number: int,
                              category: typing.Type[Warning] = PendingDeprecationWarning,
                              stacklevel: int = 1):
    """Mark supported_number of positional arguments as the maximum.

    Args:
        supported_number: Number of positional arguments
            for which no warning is raised.
        category: Type of Warning to raise
            or SKIP_DEPRECATION to return a nulldecorator
            returning the undecorated function.
        stacklevel: See :func:`warning.warn`.

    Returns:
        Return a decorator raising a category warning
            on more than supported_number positional args.

    See also:
        https://docs.python.org/3/library/exceptions.html#FutureWarning
        https://docs.python.org/3/library/exceptions.html#DeprecationWarning
        https://docs.python.org/3/library/exceptions.html#PendingDeprecationWarning
    """
    assert supported_number > 0, f'supported_number at least one: {supported_number!r}'

    if category is SKIP_DEPRECATION:
        def nulldecorator(func):
            """Return the undecorated function."""
            return func

        return nulldecorator

    assert issubclass(category, Warning)

    stacklevel += 1

    def decorator(func):
        signature = inspect.signature(func)
        argnames = [name for name, param in signature.parameters.items()
                    if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > supported_number:
                call_args = zip(argnames, args)
                supported = itertools.islice(call_args, supported_number)
                supported = dict(supported)
                deprecated = dict(call_args)
                assert deprecated
                wanted = ', '.join(f'{name}={value!r}'
                                   for name, value in deprecated.items())
                warnings.warn(f'The signature of {func.__name__} will be reduced'
                              f' to {supported_number} positional args'
                              f' {list(supported)}: pass {wanted}'
                              ' as keyword arg(s)',
                              stacklevel=stacklevel,
                              category=category)

            return func(*args, **kwargs)

        return wrapper

    return decorator
