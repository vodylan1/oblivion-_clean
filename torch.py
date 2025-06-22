"""Ultra-minimal Torch shim for unit-tests (no real math, just placeholders)."""

import types, sys
from contextlib import contextmanager


# ─────────────────────────── core Tensor object ───────────────────────────
class Tensor:  # noqa: D101
    """Dummy tensor that only carries a `.shape` tuple (and identity ops)."""

    def __init__(self, *shape):
        self.shape = shape or (1,)

    # comparisons & bit-and used by scoring-engine tests
    def __le__(self, _other):  # noqa: D401
        return Tensor()

    def __ge__(self, _other):  # noqa: D401
        return Tensor()

    def __and__(self, _other):  # noqa: D401
        return Tensor()

    # simple reshape used in tests
    def unsqueeze(self, _dim):
        self.shape = (1, *self.shape)
        return self


# identity helpers so .squeeze() / .clamp() keep same fake tensor
def _tensor_identity(self, *_, **__):
    return self


Tensor.squeeze = _tensor_identity  # y = t.squeeze()
Tensor.clamp = _tensor_identity  # y = t.clamp(...)


# allow float(tensor) in scoring code
def _tensor_float(self):  # any dummy score in [0,1]
    return 0.5


Tensor.__float__ = _tensor_float


# ───────────────────────────── fake Module base ────────────────────────────
class Module:  # noqa: D101
    """Base class for fake layers / models."""

    def eval(self, *_, **__):  # switch to eval-mode (no-op)
        return self

    def __call__(self, x, *_, **__):  # forward pass dummy
        out = Tensor()
        # If x has shape, preserve batch dimension
        out.shape = (getattr(x, "shape", (1,))[0], 1)
        return out


# ───────────────────── create torch.nn and sub-modules ─────────────────────
nn = types.ModuleType("torch.nn")
nn.Module = Module
nn.functional = types.ModuleType("torch.nn.functional")


# simple layers referenced by strategies / tests
class _FakeLayer(Module):
    def __init__(self, *_, **__):  # accept any args
        pass


nn.Linear = _FakeLayer  # type: ignore[attr-defined]
nn.ReLU = _FakeLayer  # type: ignore[attr-defined]
nn.Sequential = lambda *layers: _FakeLayer()  # type: ignore[misc]


# Parameter behaves like Tensor
class Parameter(Tensor):  # noqa: D101
    pass


nn.Parameter = Parameter  # type: ignore[attr-defined]


# ─────────────────────────── top-level helpers ─────────────────────────────
def zeros(*shape, **__):  # torch.zeros(...)
    return Tensor(*shape)


def randn(*shape, **__):  # torch.randn(...)
    return Tensor(*shape)


def tensor(data, *_, **__):  # torch.tensor([...])
    return Tensor(len(data))


float32 = "float32"  # fake dtype constant expected in tests


# no_grad context manager & torch.all shim
@contextmanager
def no_grad():  # torch.no_grad()
    yield


def all(*_, **__):  # torch.all(...)
    return True


# ─────────────────────────── sys.modules wiring ────────────────────────────
sys.modules.update(
    {
        "torch": sys.modules[__name__],
        "torch.nn": nn,
        "torch.nn.functional": nn.functional,
    }
)
