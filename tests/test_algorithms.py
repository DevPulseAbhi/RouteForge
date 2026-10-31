import networkx as nx

from algorithms import astar, bfs, dijkstra


def weighted_graph():
    graph = nx.Graph()
    graph.add_weighted_edges_from([("A", "B", 2), ("B", "C", 2), ("A", "C", 10), ("A", "D", 1), ("D", "C", 5)], weight="length")
    return graph


def test_dijkstra_returns_shortest_weighted_path():
    result = dijkstra(weighted_graph(), "A", "C")
    assert result.found and result.path == ["A", "B", "C"] and result.cost == 4


def test_astar_agrees_with_dijkstra():
    graph = weighted_graph()
    assert astar(graph, "A", "C").cost == dijkstra(graph, "A", "C").cost


def test_bfs_returns_minimum_hops_not_distance():
    result = bfs(weighted_graph(), "A", "C")
    assert result.path == ["A", "C"] and result.hops == 1 and result.cost == 10


def test_unreachable_and_invalid_nodes():
    graph = nx.Graph()
    graph.add_edge("A", "B", length=1)
    assert not dijkstra(graph, "A", "C").found
    assert bfs(graph, "A", "C").found is False
    assert "not in the graph" in dijkstra(graph, "X", "B").message


def test_source_equals_target_and_zero_weight():
    graph = nx.Graph()
    graph.add_edge(1, 2, length=0)
    result = dijkstra(graph, 1, 1)
    assert result.found and result.path == [1] and result.cost == 0
    assert astar(graph, 1, 2).cost == 0
