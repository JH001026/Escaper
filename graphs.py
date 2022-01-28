import graphviz
import math


class Building:
    def __init__(self, nodes=None, edges=None):
        if nodes is None:
            nodes = []
        self.nodes = nodes
        self.edges = edges

    def add_edge(self, e):
        self.edges.add(e)

    def add_node(self, n):
        self.nodes.add(n)

    def get_edges(self):
        return self.edges

    def get_nodes(self):
        return self.nodes

    def get_sensor_nodes(self):
        return [n for n in self.nodes if type(n) == SensorNode]

    def get_connector_nodes(self):
        return [n for n in self.nodes if type(n) == Node]

    def get_dot_rep(self):
        g = graphviz.Graph('G', engine='neato')
        g.attr('node', shape='rect')
        for n in self.get_nodes():
            g.node(n.get_name()
                   , pos=f'{n.get_x()}, {n.get_y()}!'
                   , shape=n.get_shape()
                   , color=n.get_color()
                   , label=f"{n.get_name()}\n({n.get_pop()}/{n.get_max_pop()})")
        for e in self.get_edges():
            g.edge(e.get_first().get_name(), e.get_second().get_name(), color=e.get_color())
        return g

    def get_neighbours(self, n):
        return [(o, e) for o in self.nodes for e in self.edges if o is e.get_other(n)]

    def get_node_edges(self, n):
        return [e for e in self.edges if e.get_other(n) is not None]

    def dykstra(self, source):
        dist, prev = {}, {}
        for n in self.nodes:
            dist[n] = math.inf
            prev[n] = None
        dist[source] = 0
        q = self.nodes.copy()
        while q:
            u = sorted(q, key=lambda x: dist[x])[0]
            q.remove(u)
            for (v, e) in self.get_neighbours(u):
                alt = dist[u] + e.get_weight()
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
        return prev


class Node:
    def __init__(self, name, x, y, max_pop=0, pop=0):
        self.name = name
        self.x = x / 40
        self.y = y / 40
        self.max_pop = max_pop
        self.pop = pop

    def __repr__(self):
        return f'Node {self.name} at ({self.x}, {self.y})'   # ' with pop: ({self.pop}/{self.max_pop})'

    def __str__(self):
        return f'Node {self.name} at ({self.x}, {self.y})'   # with pop: ({self.pop}/{self.max_pop})'

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_shape(self):
        return 'circle'

    def get_pop(self):
        return self.pop

    def get_max_pop(self):
        return self.max_pop

    def update_pop(self, update):
        if self.pop + update < 0:
            raise Exception("Negative population not possible")
        elif self.pop + update > self.max_pop:
            raise Exception("Population of node higher than max!")
        else:
            self.pop = self.pop + update

    def get_color(self):
        return 'red'


class SensorNode(Node):

    def get_shape(self):
        return 'rect'

    def get_color(self):
        return 'cyan'


class ExitNode(Node):

    def get_shape(self):
        return 'circle'

    def get_color(self):
        return 'green'


class Edge:
    def __init__(self, n1, n2, weight=0, color='red'):
        self.n1 = n1
        self.n2 = n2
        self.weight = weight
        self.color = color

    def __eq__(self, other):
        return (self.n1 == other.n1 and self.n2 == other.n2) or (self.n2 == other.n1 and self.n1 == other.n2)

    def get_first(self):
        return self.n1

    def get_second(self):
        return self.n2

    def get_weight(self):
        return self.weight

    def get_color(self):
        return self.color

    def get_other(self, n):
        if n == self.n1:
            return self.n2
        if n == self.n2:
            return self.n1


"""
From each node with a population
    Plot the closest path to the nearest exit (without going over population limits)

Edge case: disconnected node with population
"""

if __name__ == "__main__":
    sn_0 = SensorNode("Sensor 1", 2, 0)
    n_0 = Node('Collector 1', 2, 1)
    n_1 = Node('Collector 2', 3, 3)
    n_2 = Node('Collector 3', 1, 3)
    f_3 = Node('End 1', 1, 4)

    e0 = Edge(sn_0, n_0, 1)
    e1 = Edge(n_0, n_1, 1)
    e2 = Edge(n_0, n_2, 1)
    e3 = Edge(n_2, f_3, 3)
    e4 = Edge(n_1, f_3, 0)
    b = Building([sn_0, n_0, n_1, n_2, f_3], [e0, e1, e2, e3, e4])
    print(b.get_dot_rep())

    print(b.get_neighbours(sn_0))

    print(b.dykstra(sn_0))
