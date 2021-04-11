from typing import Callable, Generic, Protocol, TypeVar
import functools

T = TypeVar("T")
F = TypeVar("F", bound=Callable, covariant=True)


class PFuncWrapper(Protocol[F]):
    @property
    def __call__(self) -> F:
        ...


class FuncWrapper(PFuncWrapper[F]):
    def __init__(self, func: F) -> None:
        self.__root__ = func
        functools.update_wrapper(self, func)
        self.__code__ = func.__code__
        self.__defaults__ = func.__defaults__  # type: ignore
        self.__kwdefaults__ = func.__kwdefaults__  # type: ignore

    def __getattr__(self, name):
        attr = getattr(self.__root__, name)
        return attr

    def __str__(self) -> str:
        result = self.__root__.__str__()
        return result

    def __repr__(self) -> str:
        result = self.__root__.__repr__()
        return result

    @property
    def __call__(self) -> F:
        return self.__wrapped__

    @property  # type: ignore
    def __class__(self):
        return self.__wrapped__.__class__
