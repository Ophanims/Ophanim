"""Context-local physics dependencies; one world/clock/identity sequence per run."""
from contextlib import contextmanager
from contextvars import ContextVar
from itertools import count

_clock = ContextVar("physics_clock", default=None)
_world = ContextVar("physics_world", default=None)
_identity = ContextVar("physics_identity", default=None)


class ContextReference:
    def __init__(self, variable):
        object.__setattr__(self, "_variable", variable)

    def __getattr__(self, name):
        value = self._variable.get()
        if value is None:
            raise RuntimeError("Physics objects must be accessed inside their simulation session")
        return getattr(value, name)


CLOCK = ContextReference(_clock)
WORLD = ContextReference(_world)


def new_identity_sequences():
    return {"entity": count(1), "mission": count(1)}


def next_identity(kind: str) -> int:
    identity = _identity.get()
    if identity is None:
        raise RuntimeError("No active simulation identity scope")
    return next(identity[kind])


@contextmanager
def physics_context(clock, world, identity):
    tokens = [_clock.set(clock), _world.set(world), _identity.set(identity)]
    try:
        yield
    finally:
        _clock.reset(tokens[0])
        _world.reset(tokens[1])
        _identity.reset(tokens[2])
