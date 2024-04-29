import os
import json
import numpy as np
import pandas as pd
import tkinter as tk
import seaborn as sns
import scipy.special._cdflib
import matplotlib.pyplot as plt

from scipy.stats import t
from pandastable import Table
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

from PIL import Image, ImageDraw, ImageTk

enc = 'latin-1'


def create_image():
    image = Image.new('RGB', (18, 18), color='white')
    draw = ImageDraw.Draw(image)
    draw.text((-1, -1), 'A', fill='black')
    draw.text((5, -1), 'N', fill='blue')
    draw.text((11, -1), 'A', fill='green')
    draw.text((-1, 8), 'B', fill='black')
    draw.text((5, 8), 'T', fill='blue')
    draw.text((11, 8), 'M', fill='green')
    return ImageTk.PhotoImage(image)


class DataTabsApp:
    def __init__(self, root):
        self.root = root
        self.data = None
        self.event_listbox = None
        self.year_listbox = None
        self.dept_listbox = None
        self.year_data_list = None
        self.dept_data_list = None
        self.year_col = 'ANO'
        self.week_col = 'SEMANA'
        self.dept_col = 'DEPARTAMENTO'
        self.cases = 'NCASOS'
        self.year_not_grouped = "año"
        self.week_not_grouped = "semana"
        self.dept_not_grouped = "ndep_proce"
        self.count_not_grouped = "cod_eve"
        self.file_path = None; self.loaded_data = False
        self.initial_x_axis = True; self.initial_y_axis = False
        self.percentile25_lower_limit = "green"
        self.percentile50_upper_limit = "yellow"
        self.percentile75 = "red"
        self.latest_year = "black"
        self.series_name = "Serie"
        self.number_cases = "Numero de Casos"
        self.confidence = 0.95
        
        try:
            with open(os.path.join('canales_endemicos_conf',
                                   'canales_endemicos_conf.json'), 'r', encoding=enc) as conf_file:
                config = json.load(conf_file)
                self.year_col = config.get('year', 'ANO')
                self.week_col = config.get('week', 'SEMANA')
                self.dept_col = config.get('dept', 'DEPARTAMENTO')
                self.cases = config.get('cases', 'NCASOS')
                self.year_not_grouped = config.get("year_not_grouped", "año")
                self.week_not_grouped = config.get("week_not_grouped", "semana")
                self.dept_not_grouped = config.get("dept_not_grouped", "ndep_proce")
                self.count_not_grouped = config.get("count_not_grouped", "cod_eve")
                self.initial_x_axis = config.get('initial_X', True)
                self.initial_y_axis = config.get('initial_Y', False)
                self.percentile25_lower_limit = config.get("percentile25_lower_limit", "green")
                self.percentile50_upper_limit = config.get("percentile50_upper_limit", "yellow")
                self.percentile75 = config.get("percentile75", "red")
                self.latest_year = config.get("latest_year", "black")
                self.series_name = config.get("series_name", "Serie")
                self.number_cases = config.get("number_cases", "Numero de Casos")
                self.confidence = config.get('confidence', 0.95)
                
        except FileNotFoundError:
            messagebox.showwarning("Archivo de configuración NO encontrado",
                                   f"""Archivo de configuración NO encontrado en {
                                       os.path.join('canales_endemicos_conf',
                                                    'canales_endemicos_conf.json')
                                                    }\nUsando valores por defecto.""")
        self.setup_ui()

    def setup_ui(self):
        self.paned_window = ttk.PanedWindow(self.root,
                                            orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        self.left_panel = ttk.Frame(self.paned_window, width=200,
                                    height=600, relief=tk.SUNKEN)
        self.setup_left_panel()
        self.right_panel = ttk.Notebook(self.paned_window)
        self.setup_right_panel()
        self.paned_window.add(self.left_panel, weight=1)
        self.paned_window.add(self.right_panel, weight=4)

    def setup_left_panel(self, skip=False):
        ttk.Button(self.left_panel, text="Cargar Archivos de Datos",
                   command=self.load_data).pack(padx=10, pady=15)
        self.chk_state = tk.IntVar(self.left_panel)
        tk.Checkbutton(self.left_panel, text='Archivo NO Agrupado',
                       var=self.chk_state).pack(pady=10)
        ttk.Button(self.left_panel, text="Procesar Datos",
                   command=self.process_data).pack(padx=10, pady=5)
        separator = ttk.Separator(self.left_panel, orient='horizontal')
        separator.pack(fill='x', padx=10, pady=5)
        self.method = tk.StringVar(self.left_panel, value='Mediana')
        ttk.Label(self.left_panel, text='METODOLOGIA:').pack(padx=10, pady=2)
        method_combobox = ttk.Combobox(self.left_panel, textvariable=self.method,
                                       values=['Mediana', 'Bortman'])
        method_combobox.pack(padx=10, pady=10)
        method_combobox.set('Mediana')
        self.year_var = tk.StringVar(self.left_panel)
        self.dept_var = tk.StringVar(self.left_panel)
        if skip:
            self.loaded_data = False
            self.load_data()
    
    def request_column_names(self):
        prompt_window = tk.Toplevel(self.root)
        prompt_window.geometry("300x200")
        prompt_window.title("Nombres de Columnas a Agrupar")
        tk.Label(prompt_window, text="Columna AÑO:").pack()
        year_entry = tk.Entry(prompt_window)
        year_entry.pack()
        tk.Label(prompt_window, text="Columna Semana:").pack()
        week_entry = tk.Entry(prompt_window)
        week_entry.pack()
        tk.Label(prompt_window, text="Columna Departamento:").pack()
        dept_entry = tk.Entry(prompt_window)
        dept_entry.pack()
        tk.Label(prompt_window, text="Columna Casos:").pack()
        count_entry = tk.Entry(prompt_window)
        count_entry.pack()

        def set_columns():
            self.year_not_grouped = year_entry.get()
            self.week_not_grouped = week_entry.get()
            self.dept_not_grouped = dept_entry.get()
            self.count_not_grouped = count_entry.get()
            prompt_window.destroy()
            self.load_data()
        submit_button = tk.Button(prompt_window, text="Confirmar", command=set_columns)
        submit_button.pack()

    def try_to_load_base_db(self):
        while True:
            try:
                self.data = pd.read_csv(self.file_path, sep=';',
                                        encoding=enc, usecols=[self.year_not_grouped, self.week_not_grouped,
                                                                    self.dept_not_grouped, self.count_not_grouped]) if self.file_path.endswith(
                                            '.csv') else pd.read_excel(self.file_path, usecols=[self.year_not_grouped, self.week_not_grouped,
                                                                                                self.dept_not_grouped, self.count_not_grouped])
                self.loaded_data = True
                break
            except:
                self.loaded_data = False
                self.request_column_names()
                break
    
    def overwrite_base_cols_json(self):
        config_path = os.path.join('canales_endemicos_conf',
                                   'canales_endemicos_conf.json')
        os.makedirs('canales_endemicos_conf', exist_ok=True)
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding=enc) as conf_file:
                config = json.load(conf_file)
        else:
            config = {}
        config['year_not_grouped'] = self.year_not_grouped
        config['week_not_grouped'] = self.week_not_grouped
        config['dept_not_grouped'] = self.dept_not_grouped
        config['count_not_grouped'] = self.count_not_grouped
        with open(config_path, 'w', encoding=enc) as conf_file:
            json.dump(config, conf_file, indent=4)

    def load_data(self):
        if self.file_path is None:
            self.file_path = filedialog.askopenfilename(
                initialdir='.',
                filetypes=[("Excel files", "*.xlsx *.xls"),
                           ("CSV files", "*.csv")])
        if self.file_path and not self.loaded_data and any(
                y in self.file_path for y in ['.xls', '.csv']):
            self.loaded_data = True
            if self.chk_state.get() == 1:
                self.try_to_load_base_db()
                if self.loaded_data:
                    self.data = self.data.groupby([self.year_not_grouped, self.week_not_grouped, self.dept_not_grouped]
                                                ).count().reset_index()[[
                                                    self.year_not_grouped, self.week_not_grouped,
                                                    self.dept_not_grouped, self.count_not_grouped]]
                    self.data.rename(columns={self.year_not_grouped: self.year_col, self.week_not_grouped: self.week_col,
                                            self.dept_not_grouped: self.dept_col, self.count_not_grouped: self.cases},
                                            inplace=True)
                    self.overwrite_base_cols_json()
            else:
                self.data = pd.read_csv(self.file_path, sep=';',
                                        encoding=enc) if self.file_path.endswith(
                                            '.csv') else pd.read_excel(self.file_path)
            if self.loaded_data:
                if self.year_col in self.data.columns:
                    ttk.Label(self.left_panel, text="AÑO:").pack(padx=10, pady=5)
                    self.year_data_list = sorted(self.data[self.year_col].unique())
                    year_combobox = ttk.Combobox(self.left_panel, textvariable=self.year_var,
                                values=self.year_data_list)
                    year_combobox.pack(padx=10, pady=5, fill=tk.X)
                    year_combobox.bind('<<ComboboxSelected>>', self.update_year_listbox)
                    self.year_listbox = tk.Listbox(self.left_panel, selectmode='extended', exportselection=False)
                    self.year_listbox.pack(padx=10, pady=5, fill=tk.X)
                else:
                    self.prompt_for_column('AÑO')
                for col_name in self.data.columns:
                    if self.week_col in col_name:
                        self.week_col = col_name
                        break
                else:
                    self.prompt_for_column('SEMANA')
                for col_name in self.data.columns:
                    if self.dept_col in col_name:
                        self.dept_col = col_name
                        ttk.Label(self.left_panel, text="DEPARTAMENTO:").pack(padx=10, pady=5)
                        scrollbar = ttk.Scrollbar(self.left_panel, orient=tk.VERTICAL)
                        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=5)
                        self.dept_data_list = self.data[self.dept_col].unique()
                        self.dept_listbox = tk.Listbox(self.left_panel, selectmode=tk.EXTENDED,
                                                    yscrollcommand=scrollbar.set, exportselection=False)
                        scrollbar.config(command=self.dept_listbox.yview)
                        self.dept_listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
                        try:
                            self.dept_listbox.delete(0, tk.END)
                            for dept in self.dept_data_list:
                                self.dept_listbox.insert(tk.END, dept)
                        except ValueError:
                            pass
                        break
                else:
                    self.prompt_for_column('DEPARTAMENTO')
                for col_name in self.data.columns:
                    if self.cases in col_name:
                        self.cases = col_name
                        break
                else:
                    self.prompt_for_column('CONTEO CASOS')
                export_button = tk.Button(self.left_panel, text="Exportar Agrupado de Excel", command=self.export_table(self.data))
                export_button.pack(side=tk.LEFT)
        else:
            self.file_path = None
    
    def update_year_listbox(self, event=None):
        selected_year_str = self.year_var.get()
        if selected_year_str:
            try:
                selected_year = int(selected_year_str)
                self.year_listbox.delete(0, tk.END)
                for year in self.year_data_list[::-1]:
                    if year < selected_year:
                        self.year_listbox.insert(tk.END, year)
            except ValueError:
                pass

    def prompt_for_column(self, type_):
        popup = tk.Toplevel(self.root)
        popup.title(f"No se ha encontrado columna de: {type_}")
        popup.geometry("300x100")
        ttk.Label(popup, text=f"Seleccione la columna de: {type_}").pack(pady=10)
        col_var = tk.StringVar(popup)
        combobox = ttk.Combobox(popup, textvariable=col_var)
        combobox['values'] = list(self.data.columns)
        combobox.pack()

        def update_type_col():
            nonlocal col_var
            selected_col = col_var.get()
            if selected_col:
                config_path = os.path.join('canales_endemicos_conf',
                                           'canales_endemicos_conf.json')
                os.makedirs('canales_endemicos_conf', exist_ok=True)
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding=enc) as conf_file:
                        config = json.load(conf_file)
                else:
                    config = {}
                if type_ == 'AÑO':
                    self.year_col = selected_col
                    config['year'] = selected_col
                elif type_ == 'SEMANA':
                    self.week_col = selected_col
                    config['week'] = selected_col
                elif type_ == 'DEPARTAMENTO':
                    self.dept_col = selected_col
                    config['dept'] = selected_col
                elif type_ == 'CONTEO CASOS':
                    self.cases = selected_col
                    config['cases'] = selected_col
                with open(config_path, 'w', encoding=enc) as conf_file:
                    json.dump(config, conf_file, indent=4)
                for widget in self.left_panel.winfo_children():
                    widget.destroy()
                self.setup_left_panel(skip=True)
                popup.destroy()
        ttk.Button(popup, text="OK", command=update_type_col).pack(pady=10)

    def setup_right_panel(self, skip=False):
        if not skip:
            tab = ttk.Frame(self.right_panel)
            self.right_panel.add(tab, text='Sin Información')
            ttk.Label(tab,
                      text="""Seleccione la Información en el Panel de la Izquierda\n\
Posteriormente Seleccione 'Procesar Datos'""",
                      font=16).pack()
        else:
            depts = [self.dept_listbox.get(i)
                      for i in self.dept_listbox.curselection()]
            year_data_ = [int(self.year_listbox.get(i)) for i in self.year_listbox.curselection()]
            year_data_ = [int(self.year_var.get())] + (year_data_ if year_data_
                                                       else [int(i) for i in self.year_data_list
                                                             if int(self.year_var.get()) > int(i)][::-1][:4])
            tab_tabla = ttk.Frame(self.right_panel)
            tab_datos = ttk.Frame(self.right_panel)
            tab_imagen = ttk.Frame(self.right_panel)
            canales_dept = self.load_endemic_table(depts, year_data_, tab_tabla)
            if self.method.get() == 'Mediana':
                model_data = self.load_percentiles_mediana(canales_dept, year_data_, tab_datos)
            elif self.method.get() == 'Bortman':
                model_data = self.load_limits_bortman(canales_dept, year_data_, tab_datos)
            self.load_graph(model_data, year_data_,
                            canales_dept[self.dept_col].unique()[0], tab_imagen)
            self.right_panel.add(tab_imagen,
                                text=f' -Grafica de Percentiles de los Departamentos- ')
            self.right_panel.add(tab_datos,
                                text=f' -Tabla de {"Percentiles" if self.method.get() == "Mediana" else "Limites"} de los Departamentos- ')
            self.right_panel.add(tab_tabla,
                                text=f' -Tabla de Canales Endemicos de los Departamentos- ')
                

    def export_table(self, df_to_export):
        def inner_export():
            filepath = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                    filetypes=[("Excel files", "*.xlsx"),
                                                               ("All files", "*.*")])
            if filepath:
                try:
                    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                        df_to_export.to_excel(writer, index=False)
                except Exception as e:
                    print(e)
        return inner_export
    
    def load_graph(self, percentile_data, year_data_, name_, tab_imagen):
        percentiles_long = percentile_data.melt(id_vars=[self.week_col], var_name=self.series_name, value_name=self.number_cases)
        percentiles_long[self.number_cases] = pd.to_numeric(percentiles_long[self.number_cases])
        subset_year = percentiles_long[percentiles_long[self.series_name] == year_data_[0]]
        subset_others = percentiles_long[percentiles_long[self.series_name] != year_data_[0]]
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=subset_others, x=self.week_col, y=self.number_cases, hue=self.series_name, linewidth=1, palette=[
            self.percentile25_lower_limit, self.percentile50_upper_limit, self.percentile75], ax=ax)
        sns.scatterplot(data=subset_year, x=self.week_col, y=self.number_cases, hue=self.series_name, s=50, marker='o', palette=[self.latest_year], ax=ax)
        grid_X, grid_Y = self.initial_x_axis, self.initial_y_axis
        def toggle_grid_X():
            nonlocal grid_X
            grid_X = not grid_X
            ax.xaxis.grid(grid_X, which='both', linestyle='--', linewidth=0.5) if grid_X else ax.xaxis.grid(grid_X)
            canvas.draw()
        def toggle_grid_Y():
            nonlocal grid_Y
            grid_Y = not grid_Y
            ax.yaxis.grid(grid_Y, which='both', linestyle='--', linewidth=0.5) if grid_Y else ax.yaxis.grid(grid_Y)
            canvas.draw()
        def show_data_table():
            window = tk.Toplevel()
            table_frame = tk.Frame(window)
            table_frame.pack(fill='both', expand=True)
            pt = Table(table_frame, dataframe=percentiles_long, showtoolbar=True, showstatusbar=True)
            pt.show()
            screen_width = window.winfo_screenwidth() * 2 / 3
            screen_height = window.winfo_screenheight() * 2 / 3
            window.geometry(f"{int(screen_width)}x{int(screen_height)}")
        button_frame = tk.Frame(tab_imagen)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toggle_button_X = tk.Button(button_frame, text="Alternar Cuadrilla X", command=toggle_grid_X)
        toggle_button_X.pack(side=tk.LEFT)
        toggle_button_Y = tk.Button(button_frame, text="Alternar Cuadrilla Y", command=toggle_grid_Y)
        toggle_button_Y.pack(side=tk.LEFT)
        data_table_button = tk.Button(button_frame, text="Mostrar Datos en Tabla", command=show_data_table)
        data_table_button.pack(side=tk.LEFT)
        export_button = tk.Button(button_frame, text="Exportar a Excel", command=self.export_table(percentiles_long))
        export_button.pack(side=tk.LEFT)
        ax.set_xlabel(self.week_col)
        ax.set_ylabel(self.number_cases)
        ax.set_title(f'Canales endemicos {self.method.get()} {name_}')
        ax.legend(title=self.series_name)
        ax.xaxis.grid(grid_X, which='both', linestyle='--', linewidth=0.5) if grid_X else ax.xaxis.grid(grid_X)
        ax.yaxis.grid(grid_Y, which='both', linestyle='--', linewidth=0.5) if grid_Y else ax.yaxis.grid(grid_Y)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=tab_imagen)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side='top', fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(canvas, tab_imagen)
        toolbar.update()
        canvas._tkcanvas.pack(side='top', fill='both', expand=True)

    def load_percentiles_mediana(self, canales_dept, year_data_, tab_datos):
        percentiles = canales_dept.iloc[:-1, 2:].apply(lambda x: x.quantile([0.25, 0.5, 0.75])).T.reset_index()
        percentiles.rename(columns={'INDEX': self.week_col}, inplace=True)
        latest_year = pd.DataFrame(canales_dept.iloc[-1, 2:].values[None, :], columns=canales_dept.columns[2:])
        latest_year.rename(columns={'INDEX': self.week_col}, inplace=True)
        latest_year = latest_year.T.reset_index(drop=True)
        percentiles = pd.merge(percentiles, latest_year, left_index=True, right_index=True, how='inner')
        percentiles.rename(columns={0: year_data_[0]}, inplace=True)
        button_frame = tk.Frame(tab_datos)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        export_table = tk.Button(button_frame, text="Exportar a Excel", command=self.export_table(percentiles))
        export_table.pack(side=tk.LEFT)
        percent_frame = tk.Frame(tab_datos)
        percent_frame.pack_propagate(False)
        percent_frame.pack(fill="both", expand=True)
        pt = Table(percent_frame, dataframe=percentiles,
                   showtoolbar=True, showstatusbar=True,
                   width=self.right_panel.winfo_screenwidth()*2/3,
                   height=self.right_panel.winfo_screenheight()*2/3)
        pt.show()
        return percentiles
    
    def load_limits_bortman(self, canales_dept, year_data_, tab_datos):
        limites = {}
        for columna in canales_dept.iloc[:, 2:]:
            n = len(canales_dept[columna])
            media = np.exp(np.mean(np.log(canales_dept[columna])))
            desv_est_muestral = np.std(canales_dept[columna])
            error_estandar = desv_est_muestral / np.sqrt(n)
            valor_critico = -t.ppf((1 - self.confidence)/2, df=n - 1)
            limite_inferior = media - valor_critico * error_estandar
            limite_superior = media + valor_critico * error_estandar
            limites[columna] = [limite_inferior, limite_superior]
        limites = pd.DataFrame.from_dict(limites, orient='index', columns=["Limite_Inferior", "Limite_Superior"])
        latest_year = pd.DataFrame(canales_dept.iloc[-1, 2:].values[None, :], columns=canales_dept.columns[2:])
        latest_year.rename(columns={'INDEX': self.week_col}, inplace=True)
        latest_year = latest_year.T.reset_index(drop=True)
        limites = pd.merge(limites, latest_year, left_index=True, right_index=True, how='inner')
        limites.rename(columns={0: year_data_[0]}, inplace=True)
        limites.reset_index(inplace=True)
        limites.rename(columns={"index": self.week_col}, inplace=True)
        button_frame = tk.Frame(tab_datos)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        export_table = tk.Button(button_frame, text="Exportar a Excel", command=self.export_table(limites))
        export_table.pack(side=tk.LEFT)
        limit_frame = tk.Frame(tab_datos)
        limit_frame.pack_propagate(False)
        limit_frame.pack(fill="both", expand=True)
        pt = Table(limit_frame, dataframe=limites,
                   showtoolbar=True, showstatusbar=True,
                   width=self.right_panel.winfo_screenwidth()*2/3,
                   height=self.right_panel.winfo_screenheight()*2/3)
        pt.show()
        return limites

    def load_endemic_table(self, depts, year_data_, tab_data):
        dataf_comp = self.data[(self.data[self.year_col].isin(year_data_)) & (self.data[self.dept_col].isin(depts))]
        dataf_comp = dataf_comp.rename(columns={self.week_col: 'INDEX'})
        dataf_comp = dataf_comp.pivot_table(index=[self.year_col, self.dept_col], columns='INDEX', values=self.cases).reset_index()
        button_frame = tk.Frame(tab_data)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        export_table = tk.Button(button_frame, text="Exportar a Excel", command=self.export_table(dataf_comp))
        export_table.pack(side=tk.LEFT)
        datos_frame = tk.Frame(tab_data)
        datos_frame.pack_propagate(False)
        datos_frame.pack(fill="both", expand=True)
        pt = Table(datos_frame, dataframe=dataf_comp.set_index([self.year_col, self.dept_col]),
                   showtoolbar=True, showstatusbar=True,
                   width=self.right_panel.winfo_screenwidth()*2/3,
                   height=self.right_panel.winfo_screenheight()*2/3)
        pt.showIndex()
        pt.show()
        return dataf_comp

    def process_data(self):
        if self.data is not None and self.dept_listbox is not None:
            if self.year_var.get() and [
                    self.dept_listbox.get(i)
                    for i in self.dept_listbox.curselection()]:
                for widget in self.right_panel.winfo_children():
                    widget.destroy()
                self.setup_right_panel(skip=True)
    
    def cleanup(self):
        self.data = None
        self.dept_listbox = None
        self.year_listbox = None
        self.year_data_list = None
        self.file_path = None
        for widget in self.left_panel.winfo_children():
            widget.destroy()
        for widget in self.right_panel.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    icon_image = create_image()
    root.iconphoto(True, icon_image)
    root.title("Analisis de Canales Endemicos Metodologia de Mediana/Bortman")
    root.state('zoomed')
    app = DataTabsApp(root)

    def on_exit():
        app.cleanup()
        root.destroy()
        quit()

    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.mainloop()
