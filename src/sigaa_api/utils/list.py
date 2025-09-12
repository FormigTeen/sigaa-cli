from typing import TypeVar, Callable, Iterable

I = TypeVar('I')

def chunk_after(iterable: Iterable[I], pred: Callable[[I], bool]) -> Iterable[Iterable[I]]:
    out, cur = [], []
    for item in iterable:
        cur.append(item)
        if pred(item):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out
