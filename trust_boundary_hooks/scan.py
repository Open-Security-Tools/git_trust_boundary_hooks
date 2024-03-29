import re
from typing import List, NamedTuple, Tuple
from .template import Template
from .crypto import Crypto


def load_bad_symbols() -> Tuple[str, ...]:
    with open(Template().bad_symbols_path, "r") as f:
         ciphertext = f.read()

    content = Crypto().decrypt(ciphertext)
    
    def _l(line: str) -> bool:
        return (not line.startswith("#")) and line.strip()

    return tuple([x.strip() for x in content.splitlines(keepends=False) if _l(x)])


class ScanRun(NamedTuple):

    context: str
    detections: Tuple[str, ...]


class Scanner:

    def __init__(self) -> None:
        regex = "|".join(load_bad_symbols())
        self._search = re.compile(regex, re.IGNORECASE)
        self._scan_runs: List[ScanRun] = []

    def scan_string(self, context: str, value: str) -> None:
        assert isinstance(value, str)

        # Sadly we cannot optimise this search by simplifying to a set of words due to the potential for
        # regex containing white space

        matches = tuple(sorted(set(self._search.findall(value))))
        self._scan_runs.append(
            ScanRun(
                context=context,
                detections=tuple(matches),
            )
        )

    @property
    def detections(self) -> Tuple[str, ...]:
        r = set()
        for sr in self._scan_runs:
            for d in sr.detections:
                r.add(d)
        return tuple(sorted(r))

    def display_detections(self) -> None:
        for sr in self._scan_runs:
            if sr.detections:
                fl = ", ".join([f"'{x}'" for x in sr.detections])
                print(f"Context: {sr.context} -> Detections: {fl}")
