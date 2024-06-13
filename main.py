from ast import literal_eval as make_tuple
import pyproj
from pyproj import Transformer, CRS
import os
import tkintermapview
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class Backend:
    def __init__(self):
        self.selected_option = None
        self.cs1_names = []
        self.cs1_points = []
        self.cs2_cords = []
        self.cs1_x = []
        self.cs1_y = []
        self.cs1_z = []
        self.selected_cs_espg = " "
        self.cs_out = ""
        self.tree_in_headers = ("Имя точки", "B", "L", "H")
        self.tree_out_headers = ("Имя точки", "X", "Y", "H")
        self.file_opened = False

        # get custom CRS
        self.my_crs = "+init=system.crs:"

        self.cs_name = []
        self.cs_epsg = []

        line_counter = 1

        cs_data = pyproj.datadir.get_data_dir()
        cs_out = cs_data + "//system1.crs"

        with open(cs_out, 'r') as f:
            for line in f:
                if line_counter % 2 != 0:
                    self.cs_name.append(line.split()[0][1::])
                else:
                    self.cs_epsg.append(line.split()[0][1:-1])
                line_counter += 1

        f.close()

    # buttons functions
    # view on map
    def map_view(self):
        map_window = tk.Toplevel()
        map_window.geometry(f"{1000}x{800}")
        map_window.title("Map")

        map_widget = tkintermapview.TkinterMapView(map_window, width=800, height=600, corner_radius=0)
        map_widget.pack(fill="both", expand=True)
        map_widget.fit_bounding_box((56,26), (54,32))

        current_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        pin_1 = ImageTk.PhotoImage(Image.open(os.path.join(current_path, "images", "pin24.png")))

        for i in range(len(self.cs1_x)):
            marker = map_widget.set_marker(float(self.cs1_x[i]), float(self.cs1_y[i]),
                                           text=self.cs1_names[i], icon=pin_1)
        map_window.mainloop()

    # open file
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
                    else:
                        messagebox.showerror("Ошибка!", "Неверный формат")
                        break
            f.close()
            if self.file_opened:
                frontend.fill_tree_in()
            print(f"Файл {file_path} открыт")

    # selected option
    def set_selected_option(self, option):
        self.selected_option = option
        print(f"Выбранная опция: {self.selected_option}")
        for i in range(len(self.cs_name)):
            if self.selected_option == self.cs_name[i]:
                self.selected_cs_espg = self.cs_epsg[i]
                print(f"Выбрана: {self.cs_epsg[i]}")
                self.cs_out = self.my_crs + self.cs_epsg[i]
                break
            i += 1
        print(self.cs_out)

    # save file
    def save_file(self):
        file_path = filedialog.asksaveasfilename(initialdir="/", title="Сохранение файла",
                                                 defaultextension=".txt",
                                                 filetypes=(("txt files", "*.txt"),
                                                            ("all files", "*.*")))
        if file_path:
            with open(file_path+".txt", "w") as f:
                for tup in self.cs2_cords:
                    f.write(" ".join(tup) + "\n")
            f.close()
            print(f"Файл {file_path} сохранён")
            messagebox.showinfo("Сохранение файла", f"Файл {file_path} успешно сохранён.")
        else:
            print("Файл не удалось сохранить")
            messagebox.showerror("Сохранение файла", "Не удалось сохранить файл.")

    # transformation
    def transform(self):
        if self.file_opened:
            self.cs2_cords = []
            inproj = CRS.from_epsg(4326)
            outproj = CRS(self.cs_out)
            transformer_3d = Transformer.from_crs(inproj.to_3d(), outproj.to_3d())
            for i in range(len(self.cs1_x)):
                y, x, h = transformer_3d.transform(self.cs1_x[i], self.cs1_y[i], self.cs1_z[i])
                str_out = make_tuple(str((self.cs1_names[i], "%.3f" % x, "%.3f" % y, "%.3f" % h)))
                self.cs2_cords.append(str_out)
            print('Трансформировано успешно')
            return self.cs2_cords
        else:
            messagebox.showerror("Ошибка", "Исходные данные не найдены!")


# front
class Frontend:
    def __init__(self, backend):
        self.backend = backend

        # main
        self.root = tk.Tk()
        self.root.grid_columnconfigure(0, weight=1)
        self.root.minsize(640, 640)
        self.root.title("Трансформ")

        self.style = ttk.Style()
        self.style.theme_use("winnative")
        self.style.configure("Treeview.Heading", background="#CFCFCF", font=("Roboto", 11))

        # open button
        self.open_button = tk.Button(self.root, text="Открыть файл", font=("Roboto", 12),
                                     command=lambda:
                                     self.backend.open_file(self))
        self.open_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # veiw on map
        self.view_button = tk.Button(self.root, text="Показать на карте", font=("Roboto", 12),
                                     command=backend.map_view)
        self.view_button.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        # import treeview
        self.tree_in = ttk.Treeview(self.root, columns=backend.tree_in_headers, show="headings", height=10)
        for col in backend.tree_in_headers:
            self.tree_in.heading(col, text=col)
            self.tree_in.column(col, width=50, anchor="center")
        self.fill_tree_in()
        self.tree_in.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # combo box
        self.combo_label = tk.Label(self.root, text="Выберите целевую СК:", font=("Roboto", 14))
        self.combo_label.grid(row=2, column=0, padx=(10, 0), pady=10, sticky="w")
        self.combo_box = ttk.Combobox(self.root, values=backend.cs_name, font=("Roboto", 10), state="readonly",
                                      width=25)
        self.combo_box.grid(row=2, column=1, padx=(0, 105), pady=10, sticky="w")
        self.combo_box.bind("<<ComboboxSelected>>", self.on_combobox_select)

        # transform button
        self.transform_button = tk.Button(self.root, text="Трансформировать", font=("Roboto", 12),
                                          command=self.on_transform)
        self.transform_button.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        # button save
        self.transform_button = tk.Button(self.root, text="Сохранить", font=("Roboto", 12),
                                          command=backend.save_file)
        self.transform_button.grid(row=3, column=1, padx=(0, 10), pady=10, sticky="w")

        # transform treeview
        self.tree_out = ttk.Treeview(self.root, columns=backend.tree_out_headers, show="headings", height=10)
        for col in backend.tree_out_headers:
            self.tree_out.heading(col, text=col)
            self.tree_out.column(col, width=50, anchor="center")
        self.tree_out.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # root
        self.root.resizable(False, False)
        self.root.mainloop()

    def fill_tree_in(self):
        for item in self.tree_in.get_children():
            self.tree_in.delete(item)
        for item in self.backend.cs1_points:
            self.tree_in.insert('', 'end', values=item)
        self.tree_in.grid(row=1, padx=10, pady=10, sticky="ew")

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
        self.backend.set_selected_option(selected)


# init
backend = Backend()
frontend = Frontend(backend)
