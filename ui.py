from tkinter import *
from enum import Enum
from PIL import ImageTk, Image
import graphs
from graphs import Wrap
import pickle


class Mode(Enum):
    POINTER = -1
    ADD_SENSOR = 0
    ADD_COLLECTOR = 1
    ADD_END = 2


def kill_type(parent, c_type):
    for c in parent.winfo_children():
        if type(c) == c_type:
            c.destroy()


def verify_r_box(name, pop, max_pop):
    return name is not None and len(name) > 0 \
           and int(pop) >= 0 \
           and int(max_pop) >= 0 \
           and int(pop) <= int(max_pop)


def on_enter(e, top, n, name_e, cap_e, max_e):
    if verify_r_box(name_e.get(), cap_e.get(), max_e.get()):
        n.set_name(name_e.get())
        n.set_pop(int(cap_e.get()))
        n.set_max_pop(int(max_e.get()))
        top.destroy()


class UI:
    def __init__(self):
        self.window = Tk()

        self.w = 1280
        self.h = 720

        self.mode = Mode.POINTER

        self.window.title("Building Manager")

        self.window.geometry(f"{self.w}x{self.h}")

        self.window.bind('<Button-1>', self.callback)

        self.canvas = Canvas(self.window.geometry("1280x720"), width=1280, height=720)

        # self.ph = ImageTk.PhotoImage(Image.open('office.jpeg'), master=self.canvas)
        # self.canvas.create_image((150, 0), image=self.ph, anchor='nw')
        # self.canvas.update()

        self.node_grid = {}
        self.edge_map = {}
        self.selector = None
        self.selected = None
        self.top_ui = None

        btn_add_snode = Button(self.window
                               , text="Add Sensor Node"
                               , anchor="w"
                               , command=lambda: self.click_select(Mode.ADD_SENSOR)
                               , width=15)
        btn_add_snode.place(x=0, y=0)

        self.window.update()

        btn_add_cnode = Button(self.window
                               , text="Add Collector Node"
                               , anchor="w"
                               , command=lambda: self.click_select(Mode.ADD_COLLECTOR)
                               , width=15)
        btn_add_cnode.place(x=0, y=btn_add_snode.winfo_y() + btn_add_snode.winfo_height())

        self.window.update()

        btn_add_enode = Button(self.window
                               , text="Add End Node"
                               , anchor="w"
                               , command=lambda: self.click_select(Mode.ADD_END)
                               , width=15)
        btn_add_enode.place(x=0, y=btn_add_cnode.winfo_y() + btn_add_cnode.winfo_height())

        self.window.update()

        btn_gen_graph = Button(self.window
                               , text="Print Graph"
                               , anchor="w"
                               , command=lambda: self.print_graph()
                               , width=15)
        btn_gen_graph.place(x=0, y=btn_add_enode.winfo_y() + btn_add_enode.winfo_height())

        self.window.update()

        btn_save = Button(self.window
                          , text="Save!"
                          , anchor="w"
                          , command=lambda: save(self, 'yeet.pkl')
                          , width=15)
        btn_save.place(x=0, y=btn_gen_graph.winfo_y() + btn_gen_graph.winfo_height())

        self.window.update()

        btn_restore = Button(self.window
                             , text="Restore"
                             , anchor="w"
                             , command=lambda: restore(self, 'yeet.pkl')
                             , width=15)
        btn_restore.place(x=0, y=btn_save.winfo_y() + btn_save.winfo_height())

        self.window.update()

        btn_clear = Button(self.window
                             , text="Clear"
                             , anchor="w"
                             , command=lambda: self.restore({},{})
                             , width=15)
        btn_clear.place(x=0, y=btn_restore.winfo_y() + btn_restore.winfo_height())

        self.window.update()

        self.window.mainloop()

    def click_select(self, mode):
        self.mode = mode

    def callback(self, e):
        print(e.x, e.y)
        if not clickable(e.x) or self.mode == Mode.POINTER:
            return
        if self.create_node(Wrap(e.x, e.y)) is not None:
            self.on_shape_r_clicked(e)

    def create_node(self, wrap, name=None):

        o_name = gen_name(wrap)
        if gen_name(wrap) in self.node_grid.keys():
            print("Exists")
            return None

        o, n = None, None
        if self.mode == Mode.ADD_SENSOR:
            o = self.canvas.create_rectangle(get_grid_coord(wrap), fill='cyan', tags=o_name)
            n = graphs.SensorNode(self.auto_name_node(graphs.SensorNode)
                                  # , *self.translate_to_neato_coord(*get_middle(*get_grid_coord(wrap))))
                                  , get_grid_coord(wrap)[0], get_grid_coord(wrap)[1])

        elif self.mode == Mode.ADD_COLLECTOR:
            o = self.canvas.create_oval(get_grid_coord(wrap), fill='red', tags=o_name)
            n = graphs.Node(self.auto_name_node(graphs.Node)
                            # , *self.translate_to_neato_coord(*get_middle(*get_grid_coord(wrap))))
                            , get_grid_coord(wrap)[0], get_grid_coord(wrap)[1])

        elif self.mode == Mode.ADD_END:
            o = self.canvas.create_oval(get_grid_coord(wrap), fill='green', tags=o_name)
            n = graphs.ExitNode(self.auto_name_node(graphs.ExitNode)
                                # , *self.translate_to_neato_coord(*get_middle(*get_grid_coord(wrap))))
                                , get_grid_coord(wrap)[0], get_grid_coord(wrap)[1])

        self.canvas.tag_bind(o_name, '<Button-1>', self.on_shape_l_clicked)
        self.canvas.tag_bind(o_name, '<Double-Button-1>', self.on_scroll_clicked)
        # self.canvas.tag_bind(o_name, '<Button-2>', self.on_shape_double_l_clicked)
        self.canvas.tag_bind(o_name, '<Button-3>', self.on_shape_r_clicked)

        if name is None:
            name = self.auto_name_node(type(n))
        n.set_name(name)

        if o is not None:
            self.node_grid[gen_name(wrap)] = {'graphic': o, 'node': n}
            print(f'Placed: {o_name} ({n.get_x()}, {n.get_y()}')
        self.canvas.pack()
        return n

    def restore(self, saved_node_grid, saved_edge_map):
        for ui_o in [d['graphic'] for d in self.node_grid.values()] + [l for (l, e) in self.edge_map.values()]:
            self.canvas.delete(ui_o)

        self.node_grid = {}
        self.edge_map = {}

        for n in [d['node'] for d in saved_node_grid.values()]:  # Build nodes
            self.node_to_mode(n)  # Set correct mode for node
            self.create_node(Wrap(n.get_x(), n.get_y()), n.get_name())
        for e in [e for (l, e) in saved_edge_map.values()]:  # Build edges
            edge = self.create_edge(Wrap(e.get_first().get_x(), e.get_first().get_y())
                             , Wrap(e.get_second().get_x(), e.get_second().get_y()))
            edge.set_weight(e.get_weight())
            edge.set_id(e.get_id())
            self.edge_map.values()
        self.mode = Mode.POINTER

    def node_to_mode(self, node):
        if node.get_type() == graphs.NodeEnum.SensorNode:
            self.mode = Mode.ADD_SENSOR
        elif node.get_type() == graphs.NodeEnum.Node:
            self.mode = Mode.ADD_COLLECTOR
        elif node.get_type() == graphs.NodeEnum.ExitNode:
            self.mode = Mode.ADD_END
        # if type(node) is graphs.SensorNode:
        #     self.mode = Mode.ADD_SENSOR
        # elif type(node) is graphs.Node:
        #     self.mode = Mode.ADD_COLLECTOR
        # elif type(node) is graphs.ExitNode:
        #     self.mode = Mode.ADD_END

    def on_shape_l_clicked(self, e):
        if self.selected is None:
            self.remove_selector()
            self.selected = get_grid_coord(e)
            self.selector = self.canvas.create_rectangle(get_grid_coord(e), width=3, outline='black')
        self.create_edge(Wrap(e.x, e.y), Wrap(self.selected[0], self.selected[1]))

    def create_edge(self, e, sel):
        edge = None
        sel_name = gen_name_xy(sel.x, sel.y)
        print(self.node_grid)
        if self.node_grid[sel_name] is not None \
                and self.get_node(sel) is not self.get_node(e) \
                and frozenset({sel_name, gen_name(e)}) not in self.edge_map.keys():
            line = self.canvas.create_line(*get_middle(*get_grid_coord(sel)), *get_middle(*get_grid_coord(e))
                                           , arrow=LAST)
            edge = graphs.Edge(self.get_node(e), self.get_node(sel), self.auto_id_edge())
            print(edge)
            self.edge_map[frozenset({sel_name, gen_name(e)})] = (line, edge)
            self.remove_selector()
        self.canvas.pack()
        return edge

    entry_list = []

    def on_scroll_clicked(self, e):
        self.kill_all_edge_entries()

        for line, edge in self.get_n_edge_tuples(gen_name(e)):
            frame = Frame(self.window)

            label_val = Label(frame, text='W: ')
            label_val.grid(row=0, column=0)

            entry_val = Entry(frame, width=3)
            entry_val.insert(END, edge.get_weight())
            entry_val.grid(row=0, column=1)

            label_id = Label(frame, text='ID: ')
            label_id.grid(row=1, column=0)

            entry_id = Entry(frame, width=3)
            entry_id.insert(END, edge.get_id())
            entry_id.grid(row=1, column=1)

            frame.place(x=get_middle(*self.canvas.bbox(line))[0]-20, y=get_middle(*self.canvas.bbox(line))[1])

            # entry.place(*get_middle(*self.canvas.bbox(line)))
            self.entry_list.append((edge, (frame, entry_val, entry_id)))
            # self.entry_ids.append((entry_id, edge))
        for ed, en_t in self.entry_list:
            en_t[1].bind('<Return>', lambda event=e: self.kill_all_edge_entries())
            en_t[2].bind('<Return>', lambda event=e: self.kill_all_edge_entries())

    def kill_all_edge_entries(self):
        for edge, en_t in self.entry_list:
            edge.set_weight(en_t[1].get())
            edge.set_id(en_t[2].get())
        for frame in [t[1][0] for t in self.entry_list]:
            frame.destroy()
        # for entry, edge in self.entry_vals:
        #     edge.set_weight(int(entry.get()))
        #     entry.destroy()
        # for entry, edge in self.entry_ids:
        #     edge.set_id(entry.get())
        #     entry.destroy()
        self.entry_list.clear()

    def on_shape_r_clicked(self, e):
        top = Toplevel(self.window)

        if self.top_ui is not None:
            self.top_ui.destroy()
        self.top_ui = top

        node = self.get_node(e)

        frame_l = Frame(top)
        frame_r = Frame(top)
        frame_b = Frame(top)
        frame_l.grid(row=1, column=0)
        frame_r.grid(row=1, column=1)
        frame_b.grid(row=2, column=1)

        name_label = Label(top, text="Name: ")

        name_entry = Entry(top)
        name_entry.delete(0, END)
        name_entry.insert(END, self.get_node(e).get_name())
        name_entry.focus()
        name_entry.select_range(0, END)

        capacity_label = Label(frame_l, text="Population: ")

        capacity_entry = Entry(frame_l, width=2)
        capacity_entry.delete(0, END)
        capacity_entry.insert(END, self.get_node(e).get_pop())

        max_label = Label(frame_r, text="Max: ")

        max_entry = Entry(frame_r, width=2)
        max_entry.delete(0, END)
        max_entry.insert(END, self.get_node(e).get_max_pop())

        name_entry.bind('<Return>', lambda event=e: on_enter(event, top, node
                                                             , name_entry, capacity_entry, max_entry))
        capacity_entry.bind('<Return>', lambda event=e: on_enter(event, top, node
                                                                 , name_entry, capacity_entry, max_entry))
        max_entry.bind('<Return>', lambda event=e: on_enter(event, top, node
                                                            , name_entry, capacity_entry, max_entry))
        btn_burn_0 = Button(frame_b, text="Fire 1", command=lambda event=e: self.burn(node, reach=1))

        btn_burn_1 = Button(frame_b, text="Fire 2", command=lambda event=e: self.burn(node, reach=2))

        btn_ok = Button(frame_b, text="Ok", command=lambda event=e: on_enter(event, top, node
                                                                             , name_entry, capacity_entry,
                                                                             max_entry))

        btn_del = Button(frame_b, text="Delete", command=lambda x=e: self.do_destroy(e, top))

        name_label.grid(row=0, column=0, sticky="w")
        name_entry.grid(row=0, column=1)

        capacity_label.grid(row=0, column=0)
        capacity_entry.grid(row=0, column=1)

        max_label.grid(row=0, column=0)
        max_entry.grid(row=0, column=1)

        btn_ok.grid(row=0, column=0, sticky="e")
        btn_del.grid(row=0, column=1, sticky="e")
        btn_burn_0.grid(row=0, column=2, sticky="e")
        btn_burn_1.grid(row=0, column=3, sticky="e")

    def do_destroy(self, e, top):
        self.kill_all_edge_entries()
        n_name = gen_name(e)
        self.canvas.delete(self.node_grid[n_name]['graphic'])
        del self.node_grid[gen_name(e)]

        for e_set in list(self.edge_map.keys()):
            if n_name in e_set:
                self.canvas.delete(self.edge_map[e_set][0])
                del self.edge_map[e_set]

        top.destroy()
        self.remove_selector()

    def get_n_edges(self, n_name):
        return [self.edge_map[e_set][1] for e_set in self.edge_map.keys() if n_name in e_set]

    def get_n_edge_tuples(self, n_name):
        return [self.edge_map[e_set] for e_set in self.edge_map.keys() if n_name in e_set]

    def remove_selector(self):
        self.selected = None
        self.canvas.delete(self.selector)

    def print_graph(self):
        nodes = self.get_nodes()
        edges = self.get_edges()
        building = graphs.Building(nodes, edges)
        print(building.get_dot_rep(flip_y=True, di_graph=True))

    def burn(self, node, reach):
        nodes = self.get_nodes()
        edges = self.get_edges()
        building = graphs.Building(nodes, edges)
        building.detect_fire(node, reach=reach)

    def get_nodes(self):
        return [self.node_grid[k]['node'] for k in self.node_grid.keys()]

    def get_edges(self):
        return [e for (l, e) in self.edge_map.values()]

    def get_node(self, coord):
        return self.node_grid[gen_name(coord)]['node']

    def auto_name_node(self, kind):
        # return str(kind).split('.')[1].split('\'>')[0] + f"_{len([n for n in self.get_nodes() if type(n) == kind])}"
        return f'Node_{len(self.get_nodes())}'

    def auto_id_edge(self):
        return f'E_{len(self.get_edges())}'

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def translate_to_neato_coord(self, x, y):
        return x, self.h - y
        # return x, y


def get_grid_coord(e):
    g_c = 20
    return e.x - (e.x % g_c), e.y - (e.y % g_c), (e.x - (e.x % g_c)) + g_c, (e.y - (e.y % g_c)) + g_c


def gen_name(e):
    x1, y1, x2, y2 = get_grid_coord(e)
    return f'({x1},{y1})'


def gen_name_xy(x, y):
    return f'({x},{y})'


def get_middle(x1, y1, x2, y2):
    return (x1 + x2) / 2, (y1 + y2) / 2


def clickable(x):
    return x > 140


def save(process, filename):
    with open(filename, 'wb') as file:
        pickle.dump((process.node_grid, process.edge_map), file)


def restore(process, filename):
    with open(filename, 'rb') as file:
        ng, em = pickle.load(file)
        process.restore(ng, em)





if __name__ == "__main__":
    # with open('yeet.pkl', 'wb') as file:
    #     pickle.
    ui = UI()
    # with open('yeet.pkl', 'wb' ) as file:
    #     pickle.dump((ui.node_grid, ui.edge_map), file)
