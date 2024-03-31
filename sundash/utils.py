import typing as t


def get_f_self(func: t.Callable) -> object | None:
    try:
        return func.__self__
    except AttributeError:
        return None


def get_f_cls_name(func: t.Callable) -> str | None:
    name = func.__qualname__.split('.')
    if len(name) > 2:
        raise RuntimeError

    return name[0] if len(name) == 2 else None
