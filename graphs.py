import graphviz
import math
import pickle
from enum import IntEnum


class NodeEnum(IntEnum):
    SensorNode = 0
    Node = 1
    ExitNode = 2


def get_m_path_pop(route):
    return sum([n.get_max_pop() for n in route])


def get_path_pop(route):
    return sum([n.get_pop() for n in route])


def adjust_weights(path, route):
    tot_pop = get_path_pop(route[0:len(route) - 1])
    max_pop = get_m_path_pop(route[0:len(route) - 1])
    avg_pop = tot_pop / (len(route) - 1)
    if tot_pop > max_pop:
        for e in path:
            e.update_weight(avg_pop)
    for n in route:
        if avg_pop > n.get_pop():
            print(f"yeet: {n} {route} d: {avg_pop - n.get_pop()}")
            n.update_pop(avg_pop - n.get_pop())


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
        # return [n for n in self.nodes if type(n) == SensorNode]
        return [n for n in self.nodes if n.get_type() == NodeEnum.SensorNode]

    def get_connector_nodes(self):
        # return [n for n in self.nodes if type(n) == Node]
        return [n for n in self.nodes if n.get_type() == NodeEnum.Node]

    def get_dot_rep(self, coord_mod=40.0, flip_y=False, di_graph=False):
        if di_graph:
            g = graphviz.Digraph('G', engine='neato')
        else:
            g = graphviz.Graph('G', engine='neato')
        g.attr('node', shape='rect')
        for n in self.get_nodes():
            g.node(n.get_name()
                   ,
                   pos=f'{n.get_x() / coord_mod}, {720 - (n.get_y() / coord_mod) if flip_y else n.get_y() / coord_mod}!'
                   , shape=n.get_shape()
                   , color=n.get_color()
                   , label=f"{n.get_name()}\n({round(n.get_pop(), 2)}/{n.get_max_pop()})")
        for e in self.get_edges():
            g.edge(e.get_first().get_name(), e.get_second().get_name()
                   , color=e.get_color()
                   , label=f'{round(float(e.get_weight()), 2)}')
        return g

    def get_neighbours(self, n):
        return [(o, e) for o in self.nodes for e in self.edges if o is e.get_other(n)]

    def get_neighbour_nodes(self, n):
        return [o for o in self.nodes for e in self.edges if o is e.get_other(n)]

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
        return {'prev': prev, 'dist': dist}

    def get_route(self, n, p):
        route = [p]
        prev = self.dykstra(n)['prev']
        while route[0] in prev.keys() and prev[route[0]] is not None \
                and prev[route[0]] is not n and n.get_type() != NodeEnum.ExitNode:
            # and prev[route[0]] is not n and type(n) is not ExitNode:

            route = [prev[route[0]]] + route
        return [n] + route

    def get_path(self, start_n, end_n):
        route = self.get_route(start_n, end_n)
        path = []
        for i in range(len(route) - 1):
            e, rev = self.get_edge(route[i], route[i + 1])
            if rev:
                e.flip()
            path += [e]
        return path

    def has_exit(self):
        # return len([n for n in self.nodes if isinstance(n, ExitNode)]) > 0
        return len([n for n in self.nodes if n.get_type == NodeEnum.ExitNode]) > 0

    def closest_exit(self, node):
        dist = self.dykstra(node)['dist']
        # for n in dist.keys():
            # print(id(ExitNode), id(n.__class__))
            # print(is_class(n, ExitNode))
        # if len([n for n in dist.keys() if isinstance(n, ExitNode)]) == 0:
        if len([n for n in dist.keys() if n.get_type() == NodeEnum.ExitNode]) == 0:
            return None
        # return min({k: v for k, v in dist.items() if isinstance(k, ExitNode)}.items()
        return min({k: v for k, v in dist.items() if k.get_type() == NodeEnum.ExitNode}.items()
                   , key=lambda i: i[1])[0]

    def get_edge(self, n, p):
        edge = next(iter([e for e in self.edges if (e.get_first() is n or e.get_second() is n)
                          and (e.get_first() is p or e.get_second() is p)]), None)
        if edge is None:
            return None, False
        return edge, edge.get_first() is p

    def build_routes(self):
        q = list(self.nodes)
        q.sort(key=lambda node: node.get_pop())
        used_edges = []
        for n in q:
            if n.is_handled():
                continue
            if n.get_type() != NodeEnum.ExitNode:
                if (out_n := self.closest_exit(n)) is None:
                    print("No exit connected!")
                    return
                path = self.get_path(n, out_n)
                route = self.get_route(n, out_n)

                used_edges += [e for e in path if e not in used_edges]
                adjust_weights(path, route)
                for n_ in route:
                    n_.handle()
        for e in self.edges:
            if e not in used_edges:
                e.hide()
        # self.edges = used_edges
        for n in self.nodes:
            n.un_handle()
        # print(self.get_dot_rep(40, flip_y=True, di_graph=True))
        return self.get_directions()

    def get_directions(self):
        for e in [edge for edge in self.edges if edge.get_id().isdigit() and not edge.do_display()]:
            if self.get_dist_closest_exit(e.get_second()) > self.get_dist_closest_exit(e.get_first()):
                e.flip()
        return [(int(e.get_id()), e.is_flipped()) for e in self.edges if e.get_id().isdigit()]

    def get_dist_closest_exit(self, node):
        return sum([e.get_weight() for e in self.get_path(node, self.closest_exit(node))])

    def detect_fire(self, node, reach=1, weight=99999):
        if reach >= 1:
            node.set_burning()
            for (n, e) in self.get_neighbours(node):
                e.update_weight(weight)
                # self.detect_fire(n, reach - 1, int(weight / 2))
        # return self.build_routes()
        return self.build_routes()

    def reset_building(self):
        for e in self.edges:
            e.reset()
        for n in self.nodes:
            n.un_burn()

    def get_node(self, name):
        for n in self.nodes:
            if n.get_name() == name:
                return n


def is_class(n, c):
    # print(str(n.__class__), str(c))
    return str(n.__class__) == str(c)


class Node:
    def __init__(self, name, x, y, max_pop=0, pop=0):
        self.name = name
        self.x = x
        self.y = y
        self.max_pop = max_pop
        self.pop = pop
        self.handled = False
        self.burning = False

    def __repr__(self):
        return f'Node {self.name}'  # at ({self.x}, {self.y})'   # ' with pop: ({self.pop}/{self.max_pop})'

    def __str__(self):
        return f'Node {self.name}'  # at ({self.x}, {self.y})'   # with pop: ({self.pop}/{self.max_pop})'

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def handle(self):
        self.handled = True

    def is_handled(self):
        return self.handled

    def un_handle(self):
        self.handled = False

    def set_burning(self):
        if not self.burning:
            self.name = self.name   # + '🔥'
        self.burning = True

    def un_burn(self):
        if self.burning:
            self.name = self.name[:-1]
            self.burning = False

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def get_shape(self):
        return 'circle'

    def set_pop(self, pop):
        self.pop = pop

    def set_max_pop(self, max_pop):
        self.max_pop = max_pop

    def get_pop(self):
        return self.pop

    def get_max_pop(self):
        return self.max_pop

    def update_pop(self, update):
        print(f'POP UPDATE of {self.name} with {update}')
        if self.pop + update < 0:
            raise Exception("Negative population not possible")
        else:
            self.pop = self.pop + update

    def get_color(self):
        return 'red'

    def get_type(self):
        return NodeEnum.Node


class SensorNode(Node):

    def get_shape(self):
        return 'rect'

    def get_color(self):
        return 'cyan'

    def get_type(self):
        return NodeEnum.SensorNode


class ExitNode(Node):

    def get_shape(self):
        return 'circle'

    def get_color(self):
        return 'green'

    def get_type(self):
        return NodeEnum.ExitNode


class Edge:
    def __init__(self, n, p, id_s, color='green', weight=1):
        print("bruh")
        self.n = p
        self.p = n
        self.weight = weight
        self.orig_weight = weight
        self.color = color
        self.id_s = id_s
        self.flipped = False
        self.display = True

    def __eq__(self, other):
        return (self.n == other.n and self.p == other.p) or (self.p == other.n and self.n == other.p)

    def __repr__(self):
        return f'{self.n} -- {self.p} C: {self.weight}'

    def get_first(self):
        return self.n

    def get_second(self):
        return self.p

    def get_id(self):
        return self.id_s

    def set_id(self, id_s):
        self.id_s = id_s

    def is_flipped(self):
        return self.flipped

    def set_weight(self, weight):
        self.weight = weight

    def update_weight(self, weight):
        print(f"UPDATE: {weight}")
        if self.weight + weight < 1:
            raise Exception("Negative or zero-weight impossible!")
        else:
            self.weight = min(self.weight + weight, 99999)

    def do_display(self):
        return self.display

    def reset(self):
        self.weight = self.orig_weight
        self.display = True
        if self.flipped:
            self.flip()

    def hide(self):
        # print(f"HIDDEN {self.id_s}")
        self.display = False

    def get_weight(self):
        return self.weight

    def get_color(self):
        return self.color

    def get_other(self, n):
        if n == self.n:
            return self.p
        if n == self.p:
            return self.n

    def flip(self):
        self.n, self.p = self.p, self.n
        self.flipped = not self.flipped


class Wrap:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def restore(filename):
    with open(filename, 'rb') as file:
        ng, em = pickle.load(file)
        nodes = []
        edges = []
        for n in [d['node'] for d in ng.values()]:  # Build nodes
            n.set_y(n.get_y())
            nodes.append(n)
        for e in [e for (l, e) in em.values()]:  # Build edges
            e.set_weight(float(e.get_weight()))
            e.set_id(e.get_id())
            edges.append(e)
        return Building(nodes, edges)


"""
From each node with a population
    Plot the closest path to the nearest exit (without going over population limits)

Edge case: disconnected node with population
"""

if __name__ == "__main__":

    building = restore('yeet.pkl')
    # print("OG")
    print(building.get_dot_rep(flip_y=True, di_graph=True))

    print(building.detect_fire(building.get_node('A'), reach=1))
    building.reset_building()
    print(building.detect_fire(building.get_node('E'), reach=1))
    # print(building.build_routes())
    print(building.get_dot_rep(flip_y=True, di_graph=True))
    #
    # building.reset_building()
    # print(building.get_dot_rep())
