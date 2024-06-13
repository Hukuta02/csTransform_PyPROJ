from ast import literal_eval as make_tuple
import pyproj
from pyproj import Transformer, CRS
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

cs_name = []
cs_epsg = []

line_counter = 1
with open("C:/pyproj/data/system.crs", 'r') as f:
    for line in f:
        if line_counter % 2 != 0:
            cs_name.append(line.split()[0][1::])
        else:
            cs_epsg.append(line.split()[0][1:-1])
        line_counter += 1

f.close()


class Backend:
    def __init__(self):
        self.selected_option = None
        self.cs1_names = []
        self.cs1_points = []
        self.cs2_cords = ()
        self.cs1_x = []
        self.cs1_y = []
        self.cs1_z = []
        self.selected_cs_espg = " "
        self.cs_out = ""
        self.tree_in_headers = ("Имя точки", "B", "L", "H")
        self.tree_out_headers = ("Имя точки", "X", "Y", "Z")
        self.file_opened = False

        # get custom CRS
        self.my_crs = "system.crs:"

    # buttons functions
    def open_file(self, frontend):
        self.cs1_points = []
        self.cs1_x = []
        self.cs1_y = []
        self.cs1_z = []
        self.cs1_names = []

        file_path = filedialog.askopenfilename(initialdir="/", title="Выбор файла",
                                               filetypes=(("BLH files", "*.BLH"),
                                                          ("txt files", "*.txt"),
                                                          ("all files", "*.*")))
        if file_path:
            self.file_opened = True
            with open(file_path, "r") as f:
                for line in f:
                    if len(line.split()) == 4:
                        name, x, y, z = line.split()
                        point = (name, x, y, z)
                        self.cs1_points.append(point)

                        self.cs1_x.append(x)
                        self.cs1_y.append(y)
                        self.cs1_z.append(z)

                        self.cs1_names.append(name)
                        print(self.cs1_points)
                        print(type(self.cs1_points))
                    else:
                        messagebox.showerror("Ошибка!", "Неверный формат")
                        break
            f.close()
            if self.file_opened:
                frontend.fill_tree_in()
            print(f"Файл {file_path} открыт")

    def set_selected_option(self, option):
        self.selected_option = option
        print(f"Выбранная опция: {self.selected_option}")
        for i in range(len(cs_name)):
            if self.selected_option == cs_name[i]:
                self.selected_cs_espg = cs_epsg[i]
                print(f"Выбрана: {cs_epsg[i]}")
                self.cs_out = self.my_crs + cs_epsg[i]
            i += 1
        print(self.cs_out)

    def save_file(self):
        file_path = filedialog.asksaveasfilename(initialdir="/", title="Сохранение файла",
                                                 filetypes=(("txt files", "*.txt"),
                                                            ("all files", "*.*")))
        if file_path:
            with open(file_path, "w") as f:
                for tup in self.cs2_cords:
                    f.write(" ".join(tup) + "\n")
            f.close()
            print(f"Файл {file_path} сохранён")
            messagebox.showinfo("Сохранение файла", f"Файл {file_path} успешно сохранён.")
        else:
            print("Файл не удалось сохранить")
            messagebox.showerror("Сохранение файла", "Не удалось сохранить файл.")

    def transform(self):
        self.cs2_cords = []
        inproj = CRS.from_epsg(4326)
        my_crs = open("my_crs.wkt", "r").read()
        outproj = CRS.from_wkt(my_crs)
        transformer_3d = Transformer.from_crs(inproj.to_3d(), outproj.to_3d())
        for i in range(len(self.cs1_x)):
            y, x, h = transformer_3d.transform(self.cs1_x[i], self.cs1_y[i], self.cs1_z[i])
            str_out = make_tuple(str((self.cs1_names[i], "%.3f" % y, "%.3f" % x, "%.3f" % h)))
            self.cs2_cords.append(str_out)
        print(self.cs2_cords)
        print(type(self.cs2_cords))
        print('Трансформировано успешно')
        return self.cs2_cords


# front
class Frontend:
    def __init__(self, backend):
        self.backend = backend

        # main
        self.root = tk.Tk()
        self.root.minsize(640, 640)
        self.root.title("Трансформ")

        self.frame = tk.Frame(self.root)
        self.frame.pack(pady=5)

        # open button
        self.open_button = tk.Button(self.root, text="Импортировать файл", font=("Roboto", 12),
                                     command=lambda:
                                     self.backend.open_file(self))
        self.open_button.pack(anchor="nw", padx=5, pady=10)

        # import treeview
        self.tree_in = ttk.Treeview(self.root, columns=backend.tree_in_headers, show="headings", height=10)
        for col in backend.tree_in_headers:
            self.tree_in.heading(col, text=col)
            self.tree_in.column(col, width=50, anchor="center")
        self.fill_tree_in()
        #self.tree_in.pack(padx=10, pady=10, fill="both")

        # import tree scrollbar
        self.scrollbar = ttk.Scrollbar(orient="vertical", command=self.tree_in.yview)


        # combo box
        self.combo_label = tk.Label(self.root, text="Выберите СК:", font=("Roboto", 14))
        self.combo_label.pack(anchor="nw")
        self.combo_box = ttk.Combobox(self.root, values=cs_name, font=("Roboto", 10), state="readonly", width=25)
        self.combo_box.pack(anchor="nw", padx=5, pady=10)
        self.combo_box.bind("<<ComboboxSelected>>", self.on_combobox_select)

        # transform button
        self.transform_button = tk.Button(self.root, text="Трансформировать", font=("Roboto", 12),
                                          command=self.on_transform)
        self.transform_button.pack(anchor="nw", padx=5, pady=10)

        # button save
        self.transform_button = tk.Button(self.root, text="Сохранить", font=("Roboto", 12),
                                          command=backend.save_file)
        self.transform_button.pack(anchor="nw", padx=5, pady=10)

        # transform treeview
        self.tree_out = ttk.Treeview(self.root, columns=backend.tree_out_headers, show="headings", height=10)
        for col in backend.tree_out_headers:
            self.tree_out.heading(col, text=col)
            self.tree_out.column(col, width=50, anchor="center")
        self.tree_out.pack(padx=10, pady=10, fill="both")

        # root
        self.root.resizable(False, False)
        self.root.mainloop()

    def fill_tree_in(self):
        for item in self.tree_in.get_children():
            self.tree_in.delete(item)
        for item in self.backend.cs1_points:
            self.tree_in.insert('', 'end', values=item)
        self.tree_in.pack(padx=10, pady=10, fill="both")

    def on_transform(self):
        transformed_data = self.backend.transform()
        self.fill_tree_out(transformed_data)

    def fill_tree_out(self, data):
        for item in self.tree_out.get_children():
            self.tree_out.delete(item)
        for item in data:
            self.tree_out.insert("", "end", values=item)

    def on_combobox_select(self, event):
        selected = self.combo_box.get()
        self.combo_label["text"] = f"Вы выбрали: {selected}"
        self.backend.set_selected_option(selected)


# init
backend = Backend()
frontend = Frontend(backend)
