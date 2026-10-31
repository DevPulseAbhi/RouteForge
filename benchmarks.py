"""Consistent execution, validation, and comparison helpers."""

from __future__ import annotations

from typing import Callable

import networkx as nx

from algorithms import SearchResult, astar, bfs, dijkstra


def path_cost(graph: nx.Graph, path: list, weight: str = "length") -> float:
    total = 0.0
    for left, right in zip(path, path[1:]):
        data = graph.get_edge_data(left, right)
        if data is None:
            raise ValueError(f"Path uses missing edge {left!r}->{right!r}.")
        if graph.is_multigraph():
            data = min(data.values(), key=lambda item: item.get(weight, 1.0))
        value = data.get(weight, 1.0)
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Path contains an invalid edge weight.")
        total += float(value)
    return total


def path_rows(graph: nx.Graph, path: list, weight: str = "length") -> list[dict]:
    rows = []
    cumulative = 0.0
    for index, node in enumerate(path):
        node_data = graph.nodes[node]
        edge_distance = 0.0
        if index:
            data = graph.get_edge_data(path[index - 1], node)
            if graph.is_multigraph():
                data = min(data.values(), key=lambda item: item.get(weight, 1.0))
            edge_distance = float(data.get(weight, 1.0))
            cumulative += edge_distance
        rows.append({
            "Order": index + 1,
            "Node": node,
            "Latitude": node_data.get("y"),
            "Longitude": node_data.get("x"),
            "Edge distance (m)": edge_distance,
            "Cumulative distance (m)": cumulative,
        })
    return rows


def validate_result(graph: nx.Graph, source, target, result: SearchResult, weight: str = "length") -> None:
    if not result.found:
        return
    if not result.path or result.path[0] != source or result.path[-1] != target:
        raise ValueError("Algorithm returned a path with invalid endpoints.")
    measured = path_cost(graph, result.path, weight)
    if result.cost is not None and abs(measured - result.cost) > 1e-6:
        raise ValueError("Algorithm cost does not match the returned path.")


def compare_algorithms(graph: nx.Graph, source, target, weight: str = "length") -> list[SearchResult]:
    runners: list[Callable[..., SearchResult]] = [dijkstra, astar, bfs]
    results = [runner(graph, source, target, weight=weight) for runner in runners]
    for result in results:
        validate_result(graph, source, target, result, weight)
    return results
