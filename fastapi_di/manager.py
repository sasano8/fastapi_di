from typing import Type, Optional, Mapping, Callable, List, Any
from .task import Task
from .protocols import F
from inspect import getmodule


class APIRoute:
    pass


class APIRouter:
    pass


class FastInjection:
    def __init__(
        self,
        # routes: Optional[List[routing.BaseRoute]] = None,
        route_class: Type[APIRoute] = APIRoute,
        # on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        # on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        tasks: Optional[Mapping[str, Callable]] = None,
        events: Optional[Mapping[str, List[Callable[[], Any]]]] = None,
    ):
        self.router = APIRouter
        # self.routes = []
        self.route_class = route_class
        self.tasks = tasks or {}
        self.events = events or {"startup": [], "shutdown": []}

    def on_event(self, event_type: str) -> Callable:
        def wrapped(func):
            self.events[event_type].append(func)
            return func

        return wrapped

    def task(self, name: str = None) -> Callable[[F], Task[F]]:
        def wrapped(func: F) -> Task[F]:
            func_name = name or getmodule(func).__name__ + "." + func.__name__
            if func_name in self.tasks:
                raise KeyError(f"duplicate key error: name={func_name} func={func!r}")
            task = Task(func)
            self.tasks[func_name] = task
            return task

        return wrapped

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tasks={self.tasks}, events={self.events})"
