from tkinter import *
from enum import Enum
import graphs


class Mode(Enum):
    POINTER = -1
    ADD_SENSOR = 0
    ADD_COLLECTOR = 1
    ADD_END = 2


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

        self.buffer = StringVar()
        self.d1_buffer = IntVar()
        self.d2_buffer = IntVar()
        self.buffers = [self.buffer, self.d1_buffer, self.d2_buffer]

        self.selected = None

        self.node_grid = {}
        self.edge_map = {}

        self.selector = None

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
                               , text="Generate Graph"
                               , anchor="w"
                               , command=lambda: self.create_building()
                               , width=15)
        btn_gen_graph.place(x=0, y=btn_add_enode.winfo_y() + btn_add_enode.winfo_height())

        self.window.update()

        self.window.mainloop()

    def click_select(self, mode):
        self.mode = mode

    def callback(self, e):
        if not clickable(e.x):
            return

        o_name = gen_name(e)
        if o_name in self.node_grid.keys():
            return

        o, n = None, None
        if self.mode == Mode.ADD_SENSOR:
            o = self.canvas.create_rectangle(get_grid_coord(e), fill='cyan', tags=gen_name(e))
            n = graphs.SensorNode(self.auto_name(graphs.SensorNode)
                                  , *self.translate_to_neato_coord(*get_middle(*get_grid_coord(e))))

        elif self.mode == Mode.ADD_COLLECTOR:
            o = self.canvas.create_oval(get_grid_coord(e), fill='red', tags=gen_name(e))
            n = graphs.Node(self.auto_name(graphs.Node)
                            , *self.translate_to_neato_coord(*get_middle(*get_grid_coord(e))))

        elif self.mode == Mode.ADD_END:
            o = self.canvas.create_oval(get_grid_coord(e), fill='green', tags=gen_name(e))
            n = graphs.ExitNode(self.auto_name(graphs.ExitNode)
                                , *self.translate_to_neato_coord(*get_middle(*get_grid_coord(e))))

        self.canvas.tag_bind(o_name, '<Button-1>', self.on_shape_l_clicked)
        self.canvas.tag_bind(o_name, '<Button-3>', self.on_shape_r_clicked)

        if o is not None:
            self.node_grid[gen_name(e)] = {'graphic': o, 'node': n}

        self.canvas.pack()

        self.on_shape_r_clicked(e)

    def on_shape_l_clicked(self, e):
        if self.selected is None:
            self.remove_selector()
            self.selected = get_grid_coord(e)
            self.selector = self.canvas.create_rectangle(get_grid_coord(e), width=3, outline='black')
        else:
            sel_name = gen_name_xy(self.selected[0], self.selected[1])
            if self.node_grid[sel_name] is not None \
                    and self.node_grid[sel_name]['node'] is not self.node_grid[gen_name(e)]['node']:
                line = self.canvas.create_line(*get_middle(*get_grid_coord(e)), *get_middle(*self.selected))
                self.edge_map[frozenset({sel_name, gen_name(e)})] = ((line
                                                                      , graphs.Edge(self.node_grid[gen_name(e)]['node']
                                                                                    , self.node_grid[sel_name]['node']))
                )
                self.remove_selector()

        self.canvas.pack()

    def on_shape_r_clicked(self, e):
        top = Toplevel(self.window)
        node = self.node_grid[gen_name(e)]['node']

        frame_l = Frame(top)
        frame_r = Frame(top)
        frame_b = Frame(top)
        frame_l.grid(row=1, column=0)
        frame_r.grid(row=1, column=1)
        frame_b.grid(row=2, column=1)

        name_label = Label(top, text="Name: ")

        name_entry = Entry(top, textvariable=self.buffer)
        name_entry.delete(0, END)
        name_entry.insert(END, self.node_grid[gen_name(e)]['node'].get_name())
        name_entry.bind('<Return>', lambda event=e: self.on_enter(event, top, node))
        name_entry.focus()
        name_entry.select_range(0, END)

        capacity_label = Label(frame_l, text="Capacity: ")

        capacity_entry = Entry(frame_l, textvariable=self.d1_buffer, width=2)
        capacity_entry.bind('<Return>', lambda event=e: self.on_enter(event, top, node))
        capacity_entry.delete(0, END)
        capacity_entry.insert(END, '0')

        max_label = Label(frame_r, text="Max: ")

        max_entry = Entry(frame_r, textvariable=self.d2_buffer, width=2)
        max_entry.bind('<Return>', lambda event=e: self.on_enter(event, top, node))
        max_entry.delete(0, END)
        max_entry.insert(END, '0')

        btn_ok = Button(frame_b, text="Ok", command=lambda event=e: self.on_enter(event, top, node))

        btn_del = Button(frame_b, text="Delete", command=lambda x=e: self.do_destroy(e, top))

        name_label.grid(row=0, column=0, sticky="w")
        name_entry.grid(row=0, column=1)

        capacity_label.grid(row=0, column=0)
        capacity_entry.grid(row=0, column=1)

        max_label.grid(row=0, column=0)
        max_entry.grid(row=0, column=1)

        btn_ok.grid(row=0, column=0, sticky="e")
        btn_del.grid(row=0, column=1, sticky="e")

    def on_enter(self, e, top, n):
        if self.verify_inputs():
            top.destroy()
            n.set_name(self.buffer.get())

    def verify_inputs(self):
        return all([b.get() is not None and len(b.get()) > 0 for b in self.buffers if type(b) == StringVar]) \
            and self.d1_buffer.get() >= 0 \
            and self.d2_buffer.get() >= 0

    def do_destroy(self, e, top):
        n_name = gen_name(e)
        self.canvas.delete(self.node_grid[n_name]['graphic'])
        del self.node_grid[gen_name(e)]

        for e_set in list(self.edge_map.keys()):
            if n_name in e_set:
                print(self.edge_map)
                self.canvas.delete(self.edge_map[e_set][0])
                del self.edge_map[e_set]

        top.destroy()
        self.remove_selector()

    def remove_selector(self):
        self.selected = None
        self.canvas.delete(self.selector)

    def create_building(self):
        nodes = self.get_nodes()
        edges = self.get_edges()
        for n in nodes:
            print(type(n))
        b = graphs.Building(nodes, edges)
        print(b.get_dot_rep())

    def get_nodes(self):
        return [self.node_grid[k]['node'] for k in self.node_grid.keys()]

    def get_edges(self):
        return [e for (l, e) in self.edge_map.values()]

    def auto_name(self, kind):
        print(self.get_nodes())
        return str(kind).split('.')[1].split('\'>')[0] + f"_{len([n for n in self.get_nodes() if type(n) == kind])}"

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def translate_to_neato_coord(self, x, y):
        return x, self.h - y


def get_grid_coord(e):
    g_c = 20
    return e.x - (e.x % g_c), e.y - (e.y % g_c), (e.x - (e.x % g_c)) + 20, (e.y - (e.y % g_c)) + 20


def gen_name(e):
    x1, y1, x2, y2 = get_grid_coord(e)
    return f'({x1},{y1})'


def gen_name_xy(x, y):
    return f'({x},{y})'


def get_middle(x1, y1, x2, y2):
    return (x1 + x2) / 2, (y1 + y2) / 2




def clickable(x):
    return x > 140


if __name__ == "__main__":
    UI()
