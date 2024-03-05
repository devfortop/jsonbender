from functools import reduce
from itertools import chain
from warnings import warn

from jsonbender.core import Bender, bend, Transport


class ListOp(Bender):
    """
    Base class for operations on lists.
    Subclasses must implement the op() method, which takes the function passed
    to the operator's __init__(), an iterable, and should return the
    desired result.
    """
    def __init__(self, *args):
        if len(args) == 1:
            self._func = args[0]
            self._bender = None
        # TODO: this is here for compatibility reasons.
        elif len(args) == 2:
            self._bender, self._func = args
            msg = ('Passing a bender to {0} is deprecated.'
                   'Please use {0} in a composition chain '
                   '(see docs for more details).'
                   .format(type(self).__name__))
            warn(DeprecationWarning(msg))
        else:
            msg = ('{} constructor only takes one parameter, {} given'
                   .format(type(self).__name__, len(args)))
            raise TypeError(msg)

    def op(self, func, vals):
        raise NotImplementedError()

    def execute(self, source):
        # TODO: this is here for compatibility reasons
        if self._bender:
            source = self._bender(source)
        return self.op(self._func, source)


class Forall(ListOp):
    """
    Similar to Python's map().
    Builds a new list by applying the given function to each element of the
    iterable.

    Example:
    ```
    Forall(lambda i: i * 2)(range(5))  # -> [0, 2, 4, 6, 8]
    ```
    """

    def op(self, func, vals):
        if vals is None:
            return None
        return list(map(func, vals))

    @classmethod
    def bend(cls, mapping, context=None):
        """
        Return a ForallBend instance that bends each element of the list with the
        given mapping.

        mapping: a JSONBender mapping as passed to the `bend()` function.
        context: optional. the context that will be passed to `bend()`.
                 Note that if context is not passed, it defaults at bend-time
                 to the one passed to the outer mapping.

        Example:
        ```
        source = [{'a': 23}, {'a': 27}]
        bender = Forall.bend({'b': S('a')})
        bender(source)  # -> [{'b': 23}, {'b': 27}]
        ```

        """
        return ForallBend(mapping, context)


class ForallBend(Forall):
    """
    Bends each element of the list with given mapping and context.

    mapping: a JSONBender mapping as passed to the `bend()` function.
    context: optional. the context that will be passed to `bend()`.
             Note that if context is not passed, it defaults at bend-time
             to the one passed to the outer mapping.
    """

    def __init__(self, mapping, context=None):
        self._mapping = mapping
        self._context = context
        # TODO this is here for retrocompatibility reasons.
        # remove this when ListOp also breaks retrocompatibility
        self._bender = None

    def raw_execute(self, source):
        transport = Transport.from_source(source)
        context = self._context or transport.context
        # ListOp.execute assumes the func is saved on self._func
        self._func = lambda v: bend(self._mapping, v, context)
        return Transport(self.execute(transport.value), transport.context)


class Reduce(ListOp):
    """
    Similar to Python's reduce().
    Reduces an iterable into a single value by repeatedly applying the given
    function to the elements.
    The function must accept two parameters: the first is the accumulator (the
    value returned from the last call), which defaults to the first element of
    the iterable (it must be nonempty); the second is the next value from the
    iterable.

    Example: To sum a given list,
    ```
    Reduce(lambda acc, i: acc + i)([1, 4, 6])  # -> 11
    ```
    """
    def op(self, func, vals):
        try:
            return reduce(func, vals)
        except TypeError as e:  # empty list with no initial value
            raise ValueError(e.args[0])


class Filter(ListOp):
    """
    Similar to Python's filter().
    Builds a new list with the elements of the iterable for which the given
    function returns True.

    Example:
    ```
    Filter(lambda i: i % 2 == 0)(range(5))  # -> [0, 2, 4]
    ```
    """

    def op(self, func, vals):
        return list(filter(func, vals))


class FlatForall(ListOp):
    """
    Similar to Forall, but the given function must return an iterable for each
    element of the iterable, which are than "flattened" into a single
    list.

    Example:
    ```
    FlatForall(lambda x: [x-1, x+1])([1, 10, 100])  ->
         [[0, 2], [9, 11], [99, 101]] ->
         [0, 1, 9, 11, 99, 101]
    ```
    """
    def op(self, func, vals):
        return list(chain.from_iterable(map(func, vals)))
