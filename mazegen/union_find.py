"""A small disjoint-set implementation for Kruskal's algorithm."""


class DisjointSet:
    """Track connected components with compression and union by size."""

    def __init__(self, cells: list[tuple[int, int]]) -> None:
        """Create one component for every supplied cell."""
        self._parent = {cell: cell for cell in cells}
        self._size = {cell: 1 for cell in cells}

    def find(self, cell: tuple[int, int]) -> tuple[int, int]:
        """Return a component root and compress its path."""
        if self._parent[cell] != cell:
            self._parent[cell] = self.find(self._parent[cell])
        return self._parent[cell]

    def union(self, first: tuple[int, int], second: tuple[int, int]) -> bool:
        """Join two components, returning whether they were distinct."""
        root_first = self.find(first)
        root_second = self.find(second)
        if root_first == root_second:
            return False
        if self._size[root_first] < self._size[root_second]:
            root_first, root_second = root_second, root_first
        self._parent[root_second] = root_first
        self._size[root_first] += self._size[root_second]
        return True
