"""Custom graph-search algorithms used by RouteForge."""

from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush
from math import hypot
from time import perf_counter
from typing import Any, Callable, Hashable, Iterable, Mapping

import networkx as nx

Node = Hashable
Heuristic = Callable[[Node, Node], float]


@dataclass
class SearchResult:
    algorithm: str
    path: list[Node] = field(default_factory=list)
    cost: float | None = None
    explored_nodes: int = 0
    edges_considered: int = 0
    execution_time_ms: float = 0.0
    found: bool = False
    message: str = ""
    source: Node | None = None
    target: Node | None = None

    @property
    def hops(self) -> int:
        return max(0, len(self.path) - 1)


def _validate_graph_inputs(graph: nx.Graph, source: Node, target: Node) -> str | None:
    if source not in graph:
        return f"Source node {source!r} is not in the graph."
    if target not in graph:
        return f"Destination node {target!r} is not in the graph."
    return None


def _edge_weight(data: Mapping[str, Any], weight: str) -> float:
    value = data.get(weight, 1.0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Edge weight {value!r} is not numeric.")
    if value < 0:
        raise ValueError("Negative edge weights are not supported.")
    return float(value)


def _neighbors(graph: nx.Graph, node: Node, weight: str) -> Iterable[tuple[Node, Mapping[str, Any]]]:
    if graph.is_multigraph():
        for neighbor, keyed_edges in graph[node].items():
            # OSMnx MultiDiGraphs may contain parallel ways. The cheapest edge
            # is the correct relaxation candidate for a distance metric.
            data = min(keyed_edges.values(), key=lambda item: item.get(weight, 1.0))
            yield neighbor, data
    else:
        yield from graph[node].items()


def _reconstruct(previous: Mapping[Node, Node], source: Node, target: Node) -> list[Node]:
    path = [target]
    while path[-1] != source:
        if path[-1] not in previous:
            return []
        path.append(previous[path[-1]])
    path.reverse()
    return path


def dijkstra(graph: nx.Graph, source: Node, target: Node, weight: str = "length") -> SearchResult:
    """Find a minimum non-negative-weight path with a binary heap."""
    started = perf_counter()
    result = SearchResult("Dijkstra")
    result.source, result.target = source, target
    error = _validate_graph_inputs(graph, source, target)
    if error:
        result.message = error
        result.execution_time_ms = (perf_counter() - started) * 1000
        return result
    distances: dict[Node, float] = {source: 0.0}
    previous: dict[Node, Node] = {}
    queue: list[tuple[float, Node]] = [(0.0, source)]
    while queue:
        distance, node = heappop(queue)
        if distance != distances.get(node):
            continue
        result.explored_nodes += 1
        if node == target:
            result.path = _reconstruct(previous, source, target)
            result.cost = distance
            result.found = True
            break
        for neighbor, data in _neighbors(graph, node, weight):
            result.edges_considered += 1
            candidate = distance + _edge_weight(data, weight)
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                previous[neighbor] = node
                heappush(queue, (candidate, neighbor))
    if not result.found:
        result.message = "No path exists between the selected nodes."
    result.execution_time_ms = (perf_counter() - started) * 1000
    return result


def geographic_heuristic(graph: nx.Graph, node: Node, target: Node) -> float:
    """Return a straight-line lower bound in metres for OSM-style graphs."""
    a, b = graph.nodes[node], graph.nodes[target]
    if not all(key in a and key in b for key in ("x", "y")):
        return 0.0
    # OSMnx projects x/y to metres for projected graphs. For lon/lat, zero is
    # safer than mixing degrees with metre edge lengths.
    if max(abs(float(a["x"])), abs(float(b["x"]))) <= 180 and max(abs(float(a["y"])), abs(float(b["y"]))) <= 90:
        return 0.0
    return hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def astar(
    graph: nx.Graph,
    source: Node,
    target: Node,
    weight: str = "length",
    heuristic: Heuristic | None = None,
) -> SearchResult:
    """Find a weighted path using A* and an admissible graph heuristic."""
    started = perf_counter()
    result = SearchResult("A*")
    result.source, result.target = source, target
    error = _validate_graph_inputs(graph, source, target)
    if error:
        result.message = error
        result.execution_time_ms = (perf_counter() - started) * 1000
        return result
    estimate = heuristic or (lambda node, goal: geographic_heuristic(graph, node, goal))
    costs: dict[Node, float] = {source: 0.0}
    previous: dict[Node, Node] = {}
    queue: list[tuple[float, int, Node]] = [(estimate(source, target), 0, source)]
    counter = 1
    while queue:
        _, _, node = heappop(queue)
        result.explored_nodes += 1
        if node == target:
            result.path = _reconstruct(previous, source, target)
            result.cost = costs[node]
            result.found = True
            break
        for neighbor, data in _neighbors(graph, node, weight):
            result.edges_considered += 1
            candidate = costs[node] + _edge_weight(data, weight)
            if candidate < costs.get(neighbor, float("inf")):
                costs[neighbor] = candidate
                previous[neighbor] = node
                heappush(queue, (candidate + estimate(neighbor, target), counter, neighbor))
                counter += 1
    if not result.found:
        result.message = "No path exists between the selected nodes."
    result.execution_time_ms = (perf_counter() - started) * 1000
    return result


def bfs(graph: nx.Graph, source: Node, target: Node, weight: str = "length") -> SearchResult:
    """Find a minimum-hop path; edge weights are reported for context only."""
    from collections import deque

    started = perf_counter()
    result = SearchResult("BFS")
    result.source, result.target = source, target
    error = _validate_graph_inputs(graph, source, target)
    if error:
        result.message = error
        result.execution_time_ms = (perf_counter() - started) * 1000
        return result
    queue = deque([source])
    visited = {source}
    previous: dict[Node, Node] = {}
    while queue:
        node = queue.popleft()
        result.explored_nodes += 1
        if node == target:
            result.path = _reconstruct(previous, source, target)
            result.found = True
            break
        for neighbor, _ in _neighbors(graph, node, weight):
            result.edges_considered += 1
            if neighbor not in visited:
                visited.add(neighbor)
                previous[neighbor] = node
                queue.append(neighbor)
    if result.found:
        result.cost = 0.0
        for left, right in zip(result.path, result.path[1:]):
            data = graph.get_edge_data(left, right)
            if graph.is_multigraph():
                data = min(data.values(), key=lambda item: item.get(weight, 1.0))
            result.cost += _edge_weight(data, weight)
        result.message = "Minimum-hop path; not guaranteed to minimize road distance."
    else:
        result.message = "No path exists between the selected nodes."
    result.execution_time_ms = (perf_counter() - started) * 1000
    return result
