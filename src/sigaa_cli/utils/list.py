from typing import TypeVar, Callable, Optional, Union, List

I = TypeVar('I')
D = TypeVar('D')

def chunk_after(iterable: List[I], pred: Callable[[I], bool]) -> List[List[I]]:
    out, cur = [], []
    for item in iterable:
        cur.append(item)
        if pred(item):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out

def safe_get(seq: List[I], i: int, default: Optional[D] = None) -> Union[I, Optional[D]]:
    return seq[i] if -len(seq) <= i < len(seq) else default