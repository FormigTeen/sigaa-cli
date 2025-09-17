# Converter expressão booleana para FND (Forma Normal Disjuntiva)
# Suporta: ou/or/||/+ ; e/and/&&/* ; não/nao/not/!/~/¬ ; parênteses

import re
from dataclasses import dataclass
from typing import List, Union, Iterable, Set, FrozenSet

@dataclass(frozen=True)
class Var:  name: str
@dataclass(frozen=True)
class Not:  child: "Node"
@dataclass(frozen=True)
class And:  items: List["Node"]
@dataclass(frozen=True)
class Or:   items: List["Node"]
Node = Union[Var, Not, And, Or]

TOKEN_SPEC = [
    ("WS",       r"\s+"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("OR",       r"(?i:\|\||\bor\b|ou|\+|∨)"),
    ("AND",      r"(?i:&&|\band\b|e|\*|∧)"),
    ("NOT",      r"(?i:!|~|¬|\bnot\b|nao|não)"),
    ("IDENT",    r"[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ_0-9]*"),
]
MASTER_RE = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))

def tokenize(s: str):
    for m in MASTER_RE.finditer(s):
        k = m.lastgroup; v = m.group()
        if k == "WS": continue
        yield (k, v.lower() if k in {"OR","AND","NOT"} else v)
    yield ("EOF","")

class Parser:
    def __init__(self, text: str):
        self.toks = list(tokenize(text)); self.i = 0
    def peek(self): return self.toks[self.i][0]
    def take(self, kind=None):
        t = self.toks[self.i]
        if kind and t[0] != kind: raise SyntaxError(f"Esperado {kind}, encontrei {t}")
        self.i += 1; return t
    def parse(self) -> Node:
        node = self.parse_or()
        if self.peek() != "EOF": raise SyntaxError("Sobrou texto após a expressão.")
        return node
    def parse_or(self) -> Node:
        node = self.parse_and()
        while self.peek() == "OR":
            self.take("OR"); rhs = self.parse_and()
            node = Or(_flatten_or(node, rhs))
        return node
    def parse_and(self) -> Node:
        node = self.parse_factor()
        while self.peek() == "AND":
            self.take("AND"); rhs = self.parse_factor()
            node = And(_flatten_and(node, rhs))
        return node
    def parse_factor(self) -> Node:
        t = self.peek()
        if t == "NOT": self.take("NOT"); return Not(self.parse_factor())
        if t == "IDENT": return Var(self.take("IDENT")[1])
        if t == "LPAREN":
            self.take("LPAREN"); node = self.parse_or(); self.take("RPAREN"); return node
        raise SyntaxError(f"Fator inesperado: {self.toks[self.i]}")

def _flatten_or(a: Node, b: Node) -> List[Node]:
    xs=[]; 
    for x in (a,b): xs.extend(x.items) if isinstance(x, Or) else xs.append(x)
    return xs
def _flatten_and(a: Node, b: Node) -> List[Node]:
    xs=[]; 
    for x in (a,b): xs.extend(x.items) if isinstance(x, And) else xs.append(x)
    return xs

def to_nnf(node: Node, neg=False) -> Node:
    if isinstance(node, Var): return Not(node) if neg else node
    if isinstance(node, Not): return to_nnf(node.child, not neg)
    if isinstance(node, And):
        ch=[to_nnf(c,neg) for c in node.items]; return Or(ch) if neg else And(ch)
    if isinstance(node, Or):
        ch=[to_nnf(c,neg) for c in node.items]; return And(ch) if neg else Or(ch)
    raise TypeError

def _contradiction(lits: Iterable[str]) -> bool:
    pos={l for l in lits if not l.startswith("¬")}
    neg={l[1:] for l in lits if l.startswith("¬")}
    return len(pos & neg) > 0

def dnf(node: Node) -> Set[FrozenSet[str]]:
    if isinstance(node, Var): return {frozenset([node.name])}
    if isinstance(node, Not) and isinstance(node.child, Var): return {frozenset([f"¬{node.child.name}"])}
    if isinstance(node, Or):
        acc=set()
        for c in node.items: acc |= dnf(c)
        return acc
    if isinstance(node, And):
        acc={frozenset()}
        for c in node.items:
            rhs=dnf(c); new=set()
            for t1 in acc:
                for t2 in rhs:
                    merged=set(t1)|set(t2)
                    if not _contradiction(merged): new.add(frozenset(merged))
            acc=new
        return acc
    raise TypeError("AST fora de NNF ao gerar FND")

def fnd_array(expr: str):
    terms = dnf(to_nnf(Parser(expr).parse()))
    def keylit(l): return (l.startswith("¬"), l.lstrip("¬"))
    out = [sorted(list(t), key=keylit) for t in terms]
    out.sort(key=lambda xs: (len(xs), [x.lstrip("¬") for x in xs]))
    return out
