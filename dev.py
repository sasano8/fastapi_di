from typing import (
    Mapping,
    Optional,
    List,
    Callable,
    Any,
    Dict,
    Tuple,
    cast,
    Sequence,
    Type,
    TypeVar,
)
from inspect import getmodule
from fastapi.dependencies.models import Dependant as DependantBase
from pydantic.error_wrappers import ErrorWrapper
from fastapi.dependencies.utils import request_params_to_args, request_body_to_args
import asyncio
from fastapi_di.protocols import FuncMimicry
from functools import partial
from fastapi.dependencies.utils import get_typed_signature
from fastapi import params, Depends
import inspect

import asy

F = TypeVar("F", bound=Callable)


class ModelField:
    pass


def is_coroutine_callable(call: Callable[..., Any]) -> bool:
    if inspect.isroutine(call):
        return inspect.iscoroutinefunction(call)
    if inspect.isclass(call):
        return False
    call = getattr(call, "__call__", None)
    return inspect.iscoroutinefunction(call)


class Dependant(DependantBase):
    def __init__(
        self,
        *,
        body_params: Optional[List[ModelField]] = None,
        dependencies: Optional[List["Dependant"]] = None,
        name: Optional[str] = None,
        call: Optional[Callable[..., Any]] = None,
        use_cache: bool = True,
        **kwargs,  # altanative fastapi
    ) -> None:
        self.body_params = body_params or []
        self.dependencies = dependencies or []
        self.name = name
        self.call = call
        self.use_cache = use_cache
        self.cache_key = (self.call, tuple(sorted(set([]))))


def get_param_sub_dependant(*, param: inspect.Parameter) -> Dependant:
    depends: params.Depends = param.default
    if depends.dependency:
        dependency = depends.dependency
    else:
        dependency = param.annotation
    return get_sub_dependant(
        depends=depends,
        dependency=dependency,
        # path=path,
        name=param.name,
        # security_scopes=security_scopes,
    )


def get_sub_dependant(
    *,
    depends: params.Depends,
    dependency: Callable[..., Any],
    # path: str,
    name: Optional[str] = None,
    # security_scopes: Optional[List[str]] = None,
) -> Dependant:
    # security_requirement = None
    # security_scopes = security_scopes or []
    # if isinstance(depends, params.Security):
    #     dependency_scopes = depends.scopes
    #     security_scopes.extend(dependency_scopes)
    # if isinstance(dependency, SecurityBase):
    #     use_scopes: List[str] = []
    #     if isinstance(dependency, (OAuth2, OpenIdConnect)):
    #         use_scopes = security_scopes
    #     security_requirement = SecurityRequirement(
    #         security_scheme=dependency, scopes=use_scopes
    #     )
    sub_dependant = get_dependant(
        # path=path,
        call=dependency,
        name=name,
        # security_scopes=security_scopes,
        use_cache=depends.use_cache,
    )
    # if security_requirement:
    #     sub_dependant.security_requirements.append(security_requirement)
    # sub_dependant.security_scopes = security_scopes
    return sub_dependant


def add_non_field_param_to_dependency(
    *, param: inspect.Parameter, dependant: Dependant
) -> Optional[bool]:
    # if lenient_issubclass(param.annotation, Request):
    #     dependant.request_param_name = param.name
    #     return True
    return None


def get_dependant(
    *,
    call: Callable[..., Any],
    name: Optional[str] = None,
    use_cache: bool = True,
) -> Dependant:
    endpoint_signature = get_typed_signature(call)
    signature_params = endpoint_signature.parameters
    # if is_gen_callable(call) or is_async_gen_callable(call):
    #     check_dependency_contextmanagers()
    dependant = Dependant(call=call, name=name, use_cache=use_cache)
    for param_name, param in signature_params.items():
        if isinstance(param.default, params.Depends):
            sub_dependant = get_param_sub_dependant(param=param)
            dependant.dependencies.append(sub_dependant)
            continue
        if add_non_field_param_to_dependency(param=param, dependant=dependant):
            continue
        # param_field = get_param_field(
        #     param=param, default_field_info=params.Query, param_name=param_name
        # )
        # if param_name in path_param_names:
        #     assert is_scalar_field(
        #         field=param_field
        #     ), "Path params must be of one of the supported types"
        #     if isinstance(param.default, params.Path):
        #         ignore_default = False
        #     else:
        #         ignore_default = True
        #     param_field = get_param_field(
        #         param=param,
        #         param_name=param_name,
        #         default_field_info=params.Path,
        #         force_type=params.ParamTypes.path,
        #         ignore_default=ignore_default,
        #     )
        #     add_param_to_fields(field=param_field, dependant=dependant)
        # elif is_scalar_field(field=param_field):
        #     add_param_to_fields(field=param_field, dependant=dependant)
        # elif isinstance(
        #     param.default, (params.Query, params.Header)
        # ) and is_scalar_sequence_field(param_field):
        #     add_param_to_fields(field=param_field, dependant=dependant)
        # else:
        #     field_info = param_field.field_info
        #     assert isinstance(
        #         field_info, params.Body
        #     ), f"Param: {param_field.name} can only be a request body, using Body(...)"
        #     dependant.body_params.append(param_field)
    return dependant


async def solve_dependencies(
    *,
    # request: Union[Request, WebSocket],
    # dependency_overrides_provider: Optional[Any] = None,
    # response: Optional[Response] = None,
    body: Optional[Dict[str, Any]] = None,
    # background_tasks: Optional[BackgroundTasks] = None,
    dependant: Dependant,
    dependency_cache: Optional[Dict[Tuple[Callable[..., Any], Tuple[str]], Any]] = None,
) -> Tuple[
    Dict[str, Any],
    List[ErrorWrapper],
    # Optional[BackgroundTasks],
    # Response,
    Dict[Tuple[Callable[..., Any], Tuple[str]], Any],
]:
    values: Dict[str, Any] = {}
    errors: List[ErrorWrapper] = []
    dependency_cache = dependency_cache or {}
    sub_dependant: Dependant
    for sub_dependant in dependant.dependencies:
        sub_dependant.call = cast(Callable[..., Any], sub_dependant.call)
        sub_dependant.cache_key = cast(
            Tuple[Callable[..., Any], Tuple[str]], sub_dependant.cache_key
        )
        call = sub_dependant.call
        use_sub_dependant = sub_dependant
        # if (
        #     dependency_overrides_provider
        #     and dependency_overrides_provider.dependency_overrides
        # ):
        #     original_call = sub_dependant.call
        #     call = getattr(
        #         dependency_overrides_provider, "dependency_overrides", {}
        #     ).get(original_call, original_call)
        #     use_path: str = sub_dependant.path  # type: ignore
        #     use_sub_dependant = get_dependant(
        #         path=use_path,
        #         call=call,
        #         name=sub_dependant.name,
        #         security_scopes=sub_dependant.security_scopes,
        #     )
        #     use_sub_dependant.security_scopes = sub_dependant.security_scopes

        solved_result = await solve_dependencies(
            # request=request,
            dependant=use_sub_dependant,
            body=body,
            # background_tasks=background_tasks,
            # response=response,
            # dependency_overrides_provider=dependency_overrides_provider,
            dependency_cache=dependency_cache,
        )
        (
            sub_values,
            sub_errors,
            # background_tasks,
            # _,  # the subdependency returns the same response we have
            sub_dependency_cache,
        ) = solved_result
        dependency_cache.update(sub_dependency_cache)
        if sub_errors:
            errors.extend(sub_errors)
            continue
        if sub_dependant.use_cache and sub_dependant.cache_key in dependency_cache:
            solved = dependency_cache[sub_dependant.cache_key]
        # elif is_gen_callable(call) or is_async_gen_callable(call):
        #     stack = request.scope.get("fastapi_astack")
        #     if stack is None:
        #         raise RuntimeError(
        #             async_contextmanager_dependencies_error
        #         )  # pragma: no cover
        #     solved = await solve_generator(
        #         call=call, stack=stack, sub_values=sub_values
        #     )
        elif is_coroutine_callable(call):
            solved = await call(**sub_values)
        else:
            # solved = await run_in_threadpool(call, **sub_values)
            solved = call(**sub_values)
        if sub_dependant.name is not None:
            values[sub_dependant.name] = solved
        if sub_dependant.cache_key not in dependency_cache:
            dependency_cache[sub_dependant.cache_key] = solved
    # path_values, path_errors = request_params_to_args(
    #     dependant.path_params, request.path_params
    # )
    # query_values, query_errors = request_params_to_args(
    #     dependant.query_params, request.query_params
    # )
    # header_values, header_errors = request_params_to_args(
    #     dependant.header_params, request.headers
    # )
    # cookie_values, cookie_errors = request_params_to_args(
    #     dependant.cookie_params, request.cookies
    # )
    # values.update(path_values)
    # values.update(query_values)
    # values.update(header_values)
    # values.update(cookie_values)
    # errors += path_errors + query_errors + header_errors + cookie_errors
    if dependant.body_params:
        (
            body_values,
            body_errors,
        ) = await request_body_to_args(  # body_params checked above
            required_params=dependant.body_params, received_body=body
        )
        values.update(body_values)
        errors.extend(body_errors)
    # if dependant.http_connection_param_name:
    #     values[dependant.http_connection_param_name] = request
    # if dependant.request_param_name and isinstance(request, Request):
    #     values[dependant.request_param_name] = request
    # elif dependant.websocket_param_name and isinstance(request, WebSocket):
    #     values[dependant.websocket_param_name] = request
    # if dependant.background_tasks_param_name:
    #     if background_tasks is None:
    #         background_tasks = BackgroundTasks()
    #     values[dependant.background_tasks_param_name] = background_tasks
    # if dependant.response_param_name:
    #     values[dependant.response_param_name] = response
    # if dependant.security_scopes_param_name:
    #     values[dependant.security_scopes_param_name] = SecurityScopes(
    #         scopes=dependant.security_scopes
    #     )
    # return values, errors, background_tasks, response, dependency_cache
    return values, errors, dependency_cache


class Task(FuncMimicry[F]):
    @property
    def do(self) -> F:
        """inject dependency and call."""
        return self._do
        # injected = partial(self.__root__)  # type: ignore
        # return lambda *args, **kwargs: injected(*args, **kwargs)  # type: ignore

    async def _do(self, **kwargs):
        dependant = get_dependant(call=self)
        values, errors, dependency_cache = await solve_dependencies(
            dependant=dependant, body=kwargs
        )
        return await self(**values)

    async def resolve_dependency(self, **kwargs):

        # dependant = Dependant(call=self)
        dependant = get_dependant(call=self)
        return await solve_dependencies(dependant=dependant)


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


async def main():
    app = FastInjection()

    @app.on_event("startup")
    def test():
        pass

    def get_user_id():
        import random

        return random.random()

    @app.task()
    def func(value=1):
        return value

    @app.task()
    async def func2(user_id: int = Depends(get_user_id)):
        return user_id

    # assert func.do(value=3) == 3
    values, errors, dependency_cache = await func2.resolve_dependency()
    print(f"{values=} {errors=} {dependency_cache=}")

    # values, errors, dependency_cache = await func2.resolve_dependency()
    # print(f"{values=} {errors=} {dependency_cache=}")

    result = await func2.do(user_id=3)
    assert result

    print(repr(app))


"""
body_paramsとは何か？
Dependantで直接生成するのでなく、get_dependantで生成する。

"""