import networkx as nx
import pytest

from benchmarks import compare_algorithms, path_cost
from road_network import closure_copy, nearest_node, radius_to_metres, route_bbox, route_coordinates


def graph():
    result = nx.MultiDiGraph()
    result.add_node(1, x=0, y=0)
    result.add_node(2, x=1, y=0)
    result.add_node(3, x=2, y=0)
    result.add_edge(1, 2, length=1)
    result.add_edge(2, 3, length=1)
    return result


def test_snapping_and_route_coordinates():
    result = graph()
    assert nearest_node(result, 0.1, 0.1) == 1
    assert route_coordinates(result, [1, 2]) == [(0.0, 0.0), (0.0, 1.0)]


def test_closure_does_not_mutate_original():
    original = graph()
    changed = closure_copy(original, (1, 2, 0))
    assert original.has_edge(1, 2) and not changed.has_edge(1, 2)


def test_comparison_shape_and_invalid_weight():
    result = compare_algorithms(graph(), 1, 3)
    assert {item.algorithm for item in result} == {"Dijkstra", "A*", "BFS"}
    assert all(item.execution_time_ms >= 0 for item in result)
    bad = nx.Graph()
    bad.add_edge(1, 2, length="bad")
    with pytest.raises(ValueError):
        path_cost(bad, [1, 2])


def test_route_bbox_contains_both_locations():
    west, south, east, north = route_bbox((12.9, 77.5), (13.1, 77.7), 0.01)
    assert west < 77.5 < east
    assert west < 77.7 < east
    assert south < 12.9 < north
    assert south < 13.1 < north


def test_radius_is_converted_from_kilometres_to_metres():
    assert radius_to_metres(60) == 60_000
    assert radius_to_metres(150) == 150_000
    with pytest.raises(ValueError):
        radius_to_metres(0)
