import os
import json
import numpy as np
import pandas as pd
import tkinter as tk
import matplotlib.pyplot as plt

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
    draw.text((-1, 8), 'C', fill='black')
    draw.text((5, 8), 'O', fill='blue')
    draw.text((11, 8), 'M', fill='green')
    return ImageTk.PhotoImage(image)


class DataTabsApp:
    def __init__(self, root):
        self.root = root
        self.data = None
        self.event_listbox = None
        self.year_listbox = None
        self.year_data_list = None
        self.year_col = 'ANO'; self.week_col = 'SEMANA'
        self.file_path = None; self.loaded_data = False
        self.initial_x_axis = True; self.initial_y_axis = False
        self.increasing_ratio_color= "orange"; self.decreasing_ratio_color= "gray"
        self.increasing_complement_color= "blue"; self.decreasing_complement_color= "black"
        self.observed_color= "red"; self.expected_color= "purple"
        try:
            with open(os.path.join('comportamiento_mmwr_conf',
                                   'comportamiento_mmwr_conf.json'), 'r', encoding=enc) as conf_file:
                config = json.load(conf_file)
                self.year_col = config.get('year', 'ANO')
                self.week_col = config.get('week', 'SEMANA')
                self.initial_x_axis = config.get('initial_X', True)
                self.initial_y_axis = config.get('initial_Y', False)
                self.increasing_ratio_color = config.get("increasing_ratio_color", "orange")
                self.decreasing_ratio_color = config.get("decreasing_ratio_color", "gray")
                self.increasing_complement_color = config.get("increasing_complement_color", "blue")
                self.decreasing_complement_color = config.get("decreasing_complement_color", "black")
                self.observed_color = config.get("observed_color", "red")
                self.expected_color = config.get("expected_color", "purple")
        except FileNotFoundError:
            messagebox.showwarning("Archivo de configuración NO encontrado",
                                   f"""Archivo de configuración NO encontrado en {
                                       os.path.join('comportamiento_mmwr_conf',
                                                    'comportamiento_mmwr_conf.json')
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
        ttk.Button(self.left_panel, text="Procesar Datos",
                   command=self.process_data).pack(padx=10, pady=5)
        self.year_var = tk.StringVar(self.left_panel)
        self.week_var = tk.StringVar(self.left_panel)
        self.event_var = tk.StringVar(self.left_panel)
        scrollbar = ttk.Scrollbar(self.left_panel, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=5)
        self.event_listbox = tk.Listbox(self.left_panel, selectmode=tk.EXTENDED,
                                        yscrollcommand=scrollbar.set, exportselection=False)
        scrollbar.config(command=self.event_listbox.yview)
        if skip:
            self.loaded_data = False
            self.load_data()

    def load_data(self):
        if self.file_path is None:
            self.file_path = filedialog.askopenfilename(
                initialdir='.',
                filetypes=[("Excel files", "*.xlsx *.xls"),
                           ("CSV files", "*.csv")])
        if self.file_path and not self.loaded_data and any(
                y in self.file_path for y in ['.xls', '.csv']):
            self.loaded_data = True
            self.data = pd.read_csv(self.file_path,
                                    encoding=enc) if self.file_path.endswith(
                                        '.csv') else pd.read_excel(self.file_path)
            self.data.columns = [col for col in self.data.columns]
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
                    ttk.Label(self.left_panel,
                              text="SEMANA:").pack(padx=10, pady=5)
                    ttk.Combobox(self.left_panel, textvariable=self.week_var,
                                 values=sorted(self.data[self.week_col].unique())
                                 ).pack(padx=10, pady=5, fill=tk.X)
                    break
            else:
                self.prompt_for_column('SEMANA')
            if len(self.data.columns) > 2:
                ttk.Label(self.left_panel, text="EVENTO:").pack(padx=10, pady=5)
                for event in [col for col in self.data.columns
                              if col not in [self.year_col, self.week_col]]:
                    self.event_listbox.insert(tk.END, event)
                self.event_listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
                self.left_panel.pack_propagate(False)
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
                config_path = os.path.join('comportamiento_mmwr_conf',
                                           'comportamiento_mmwr_conf.json')
                os.makedirs('comportamiento_mmwr_conf', exist_ok=True)
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
            year = self.year_var.get()
            week = self.week_var.get()
            events = [self.event_listbox.get(i)
                      for i in self.event_listbox.curselection()]
            tab_tabla = ttk.Frame(self.right_panel)
            self.right_panel.add(tab_tabla,
                                 text=f' -Tabla de Periodo de los Eventos Seleccionados- ')
            tablas_por_evento = self.load_event_table(year, week,
                                                      events, tab_tabla)
            tab_datos = ttk.Frame(self.right_panel)
            self.right_panel.add(tab_datos,
                                 text=f' -Tabla de Datos de los Eventos Seleccionados- ')
            cat, obs, esp, raz = self.load_data_table(year, tab_datos,
                                                 tablas_por_evento)
            tab_imagen = ttk.Frame(self.right_panel)
            self.right_panel.add(tab_imagen,
                                 text=f' -Grafica de Datos de los Eventos Seleccionados- ')
            self.load_data_graph(cat, obs, esp, tab_imagen)

            tab_imagen_diff = ttk.Frame(self.right_panel)
            self.right_panel.add(tab_imagen_diff,
                                 text=f' -Grafica de Diferencias de los Eventos Seleccionados- ')
            self.load_diff_graph(cat, raz, esp, tab_imagen_diff)
    
    def export_table(self, df_to_export):
        def inner_export():
            filepath = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
            if filepath:
                try:
                    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                        df_to_export.to_excel(writer, index=False)
                except Exception as e:
                    pass
        return inner_export
    
    def load_diff_graph(self, cat, raz, esp, tab_imagen_diff):
        graph_data = {'Categoria': cat,
                      'Razon': raz,
                      'Esperado': esp}
        df = pd.DataFrame(graph_data)
        df.sort_values('Razon', inplace=True)
        fig, ax = plt.subplots(figsize=(10, 6))
        colors_1 = [self.increasing_ratio_color if x >= 1 else self.decreasing_ratio_color for x in df['Razon']]
        colors_2 = [self.increasing_complement_color if x >= 1 else self.decreasing_complement_color for x in df['Esperado']]
        df['Adjusted_Razon'] = df['Razon'] - 1
        df['Adjusted_Esperado'] = df['Esperado'] - 1
        labels = {self.decreasing_ratio_color: 'Razón Disminuye', self.increasing_complement_color: 'Complemento Aumenta',
                  self.decreasing_complement_color: 'Complemento Disminuye', self.increasing_ratio_color: 'Razón Aumenta'}
        for i in range(len(df)):
            razon_length = abs(df['Adjusted_Razon'].iloc[i])
            esperado_length = abs(df['Adjusted_Esperado'].iloc[i])    
            if razon_length >= esperado_length:
                ax.barh(i, df['Adjusted_Razon'].iloc[i], left=1, color=colors_2[i],
                        edgecolor='black', height=0.35, label=labels[colors_2[i]])
                ax.barh(i, df['Adjusted_Esperado'].iloc[i], left=1, color=colors_1[i],
                        edgecolor='black', height=0.35, label=labels[colors_1[i]])
            else:
                ax.barh(i, df['Adjusted_Esperado'].iloc[i], left=1, color=colors_1[i],
                        edgecolor='black', height=0.35, label=labels[colors_1[i]])
                ax.barh(i, df['Adjusted_Razon'].iloc[i], left=1, color=colors_2[i],
                        edgecolor='black', height=0.35, label=labels[colors_2[i]])
        grid_X, grid_Y = self.initial_x_axis, self.initial_y_axis
        button_frame = tk.Frame(tab_imagen_diff)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
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
            pt = Table(table_frame, dataframe=df, showtoolbar=True, showstatusbar=True)
            pt.show()
            screen_width = window.winfo_screenwidth() * 2 / 3
            screen_height = window.winfo_screenheight() * 2 / 3
            window.geometry(f"{int(screen_width)}x{int(screen_height)}")
        toggle_button_X = tk.Button(button_frame, text="Alternar Cuadrilla X", command=toggle_grid_X)
        toggle_button_X.pack(side=tk.LEFT)
        toggle_button_Y = tk.Button(button_frame, text="Alternar Cuadrilla Y", command=toggle_grid_Y)
        toggle_button_Y.pack(side=tk.LEFT)
        data_table_button = tk.Button(button_frame, text="Mostrar Datos en Tabla", command=show_data_table)
        data_table_button.pack(side=tk.LEFT)
        export_table = tk.Button(button_frame, text="Exportar a Excel", command=self.export_table(df))
        export_table.pack(side=tk.LEFT)
        ax.set_yticks(range(len(df['Categoria'])))
        ax.set_yticklabels(df['Categoria'])
        ax.set_xlabel('Razón')
        ax.set_title('Razón de Observado a Esperado')
        ax.set_xlim(min(df['Razon']) - 0.1, max(df['Razon']) + 0.1)
        ax.xaxis.grid(grid_X, which='both', linestyle='--', linewidth=0.5) if grid_X else ax.xaxis.grid(grid_X)
        ax.yaxis.grid(grid_Y, which='both', linestyle='--', linewidth=0.5) if grid_Y else ax.yaxis.grid(grid_Y)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=tab_imagen_diff)
        canvas.draw()
        canvas.get_tk_widget().pack(side='top',
                                    fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(canvas, tab_imagen_diff)
        toolbar.update()
        canvas._tkcanvas.pack(side='top', fill='both', expand=True)
        
    def load_data_graph(self, cat, obs, esp, tab_imagen):
        graph_data = {'Categoria': cat,
                      'Esperado': list(np.array(esp)*np.array(obs)),
                      'Observado': obs}
        df = pd.DataFrame(graph_data)
        fig, ax = plt.subplots(figsize=(10, 5))
        observado_mask = df['Observado'] > df['Esperado']
        esperado_mask = ~observado_mask
        for i in range(len(df)):
            if observado_mask[i]:
                ax.barh(i, df['Observado'][i], color=self.observed_color, edgecolor='black',
                        height=0.35, label='Observado' if i == 0 else "")
                ax.barh(i, df['Esperado'][i], color=self.expected_color, edgecolor='black',
                        height=0.35, label='Esperado' if i == 0 else "")
            elif esperado_mask[i]:
                ax.barh(i, df['Esperado'][i], color=self.expected_color, edgecolor='black',
                        height=0.35, label='Esperado' if i == 0 else "")
                ax.barh(i, df['Observado'][i], color=self.observed_color, edgecolor='black',
                        height=0.35, label='Observado' if i == 0 else "")
        grid_X, grid_Y = self.initial_x_axis, self.initial_y_axis
        button_frame = tk.Frame(tab_imagen)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
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
            pt = Table(table_frame, dataframe=df, showtoolbar=True, showstatusbar=True)
            pt.show()
            screen_width = window.winfo_screenwidth() * 2 / 3
            screen_height = window.winfo_screenheight() * 2 / 3
            window.geometry(f"{int(screen_width)}x{int(screen_height)}")
        toggle_button_X = tk.Button(button_frame, text="Alternar Cuadrilla X", command=toggle_grid_X)
        toggle_button_X.pack(side=tk.LEFT)
        toggle_button_Y = tk.Button(button_frame, text="Alternar Cuadrilla Y", command=toggle_grid_Y)
        toggle_button_Y.pack(side=tk.LEFT)
        data_table_button = tk.Button(button_frame, text="Mostrar Datos en Tabla", command=show_data_table)
        data_table_button.pack(side=tk.LEFT)
        export_table = tk.Button(button_frame, text="Exportar a Excel", command=self.export_table(df))
        export_table.pack(side=tk.LEFT)
        ax.set_title('Comportamientos Inusuales')
        ax.set_xlabel('Cantidad de Eventos')
        ax.set_ylabel('Eventos')
        ax.set_yticks(range(len(df['Categoria'])))
        ax.set_yticklabels(df['Categoria'])
        ax.xaxis.grid(grid_X, which='both', linestyle='--', linewidth=0.5) if grid_X else ax.xaxis.grid(grid_X)
        ax.yaxis.grid(grid_Y, which='both', linestyle='--', linewidth=0.5) if grid_Y else ax.yaxis.grid(grid_Y)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=tab_imagen)
        canvas.draw()
        canvas.get_tk_widget().pack(side='top',
                                    fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(canvas, tab_imagen)
        toolbar.update()
        canvas._tkcanvas.pack(side='top', fill='both', expand=True)
    
    def load_data_table(self, year, tab_datos, tablas_por_evento):
        year = int(year)
        cat, obs, esp, raz, event_info = [], [], [], [], {}
        button_frame = tk.Frame(tab_datos)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        for evento, tabla in tablas_por_evento.items():
            temp_table = tabla[tabla[self.year_col] != year]
            media = temp_table[evento].mean()
            observado = tabla[(tabla[self.year_col] == year) &
                              (tabla['PERIODO'] == 'CENTRAL')][evento].values[0]
            desviacion_estandar = temp_table[evento].std()
            coeficiente_variacion = (desviacion_estandar / media) * 100
            limite_superior = 1 + 1.96 * coeficiente_variacion
            limite_inferior = 1 - 1.96 * coeficiente_variacion
            razon = observado / media if media != 0 else float('inf')
            esperado_f = 0
            if razon > limite_superior:
                esperado_f = limite_superior
            elif razon < limite_inferior:
                esperado_f = limite_inferior
            else:
                esperado_f=razon
            cat.append(evento)
            obs.append(observado)
            esp.append(esperado_f)
            raz.append(razon)
            event_info[evento] = {'Promedio': media,
                                  'Desviación Estándar': desviacion_estandar,
                                  'Observado':observado,
                                  'Coeficiente de Variación': coeficiente_variacion,
                                  'razón':razon,
                                  'esperado':esperado_f,
                                  'Límite Superior': limite_superior,
                                  'Límite Inferior': limite_inferior}
        export_table = tk.Button(button_frame, text="Exportar a Excel", command=self.export_table(
            pd.DataFrame(event_info).reset_index()))
        export_table.pack(side=tk.LEFT)
        datos_frame = tk.Frame(tab_datos)
        datos_frame.pack_propagate(False)
        datos_frame.pack(fill="both", expand=True)
        pt = Table(datos_frame, dataframe=pd.DataFrame(event_info).reset_index(),
                   showtoolbar=True, showstatusbar=True,
                   width=self.right_panel.winfo_screenwidth()*2/3,
                   height=self.right_panel.winfo_screenheight()*2/3)
        pt.show()
        return cat, obs, esp, raz

    def load_event_table(self, year, week, events, tab_tabla):
        year, week = int(year), int(week)
        button_frame = tk.Frame(tab_tabla)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        periodos_historicos = pd.DataFrame()
        year_data_ = [int(self.year_listbox.get(i)) for i in self.year_listbox.curselection()]
        year_data_ = year_data_ if year_data_ else [i for i in self.year_data_list if year > i][::-1][:5]
        for year_var in ([year] + year_data_):
            semanas_anteriores = [week - i for i in range(7, 3, -1)]
            semanas_centrales = [week - i for i in range(3, -1, -1)]
            semanas_posteriores = [week + i for i in range(1, 5)]
            periodo_anterior = self.data.loc[(self.data[self.week_col].isin(
                semanas_anteriores)) & (self.data[self.year_col] == year_var)].copy()
            periodo_central = self.data.loc[(self.data[self.week_col].isin(
                semanas_centrales)) & (self.data[self.year_col] == year_var)].copy()
            periodo_posterior = self.data.loc[(self.data[self.week_col].isin(
                semanas_posteriores)) & (self.data[self.year_col] == year_var)].copy()
            try:
                max_week_previous_year = max(self.data.loc[self.data[self.year_col] ==
                                                           year_var - 1, self.week_col].values)
                previous_year_semanas_anteriores = [max_week_previous_year + week_
                                                    for week_ in semanas_anteriores if week_ < 1]
                previous_year_semanas_centrales = [max_week_previous_year + week_
                                                   for week_ in semanas_centrales if week_ < 1]
                if previous_year_semanas_anteriores:
                    periodo_anterior_prev_year = self.data.loc[(self.data[self.week_col].isin(
                        previous_year_semanas_anteriores)) &
                        (self.data[self.year_col] == year_var - 1)].copy()
                    periodo_anterior = pd.concat([periodo_anterior, periodo_anterior_prev_year])
                    periodo_anterior[self.year_col] = year_var
                if previous_year_semanas_centrales:
                    periodo_central_prev_year = self.data.loc[(self.data[self.week_col].isin(
                        previous_year_semanas_centrales)) &
                        (self.data[self.year_col] == year_var - 1)].copy()
                    periodo_central = pd.concat([periodo_central, periodo_central_prev_year])
                    periodo_central[self.year_col] = year_var
            except:
                pass
            try:
                max_week_this_year = max(self.data.loc[self.data[self.year_col] ==
                                                       year_var, self.week_col].values)
                next_year_semanas_posteriores = [(week_ - max_week_this_year)
                                                 for week_ in semanas_posteriores if week_ > max_week_this_year]
                if next_year_semanas_posteriores:
                    periodo_posterior_next_year = self.data.loc[(self.data[self.week_col].isin(
                        next_year_semanas_posteriores)) &
                        (self.data[self.year_col] == year_var + 1)].copy()
                    periodo_posterior = pd.concat([periodo_posterior, periodo_posterior_next_year])
                    periodo_posterior[self.year_col] = year_var
            except:
                pass
            periodo_anterior['PERIODO'] = 'ANTERIOR'
            periodo_central['PERIODO'] = 'CENTRAL'
            periodo_posterior['PERIODO'] = 'POSTERIOR'
            periodos_anuales = pd.concat([periodo_anterior, periodo_central, periodo_posterior])
            periodos_anuales_suma = periodos_anuales.groupby(
                [self.year_col, 'PERIODO'])[events].sum().reset_index()
            periodos_historicos = pd.concat([periodos_historicos, periodos_anuales_suma])
        combined_data, tablas_por_evento = pd.DataFrame(), {}
        for evento in events:
            event_data = periodos_historicos[[self.year_col, 'PERIODO', evento]].copy()
            tablas_por_evento[evento] = periodos_historicos[[self.year_col,
                                                             'PERIODO', evento]].copy()
            if combined_data.empty:
                combined_data = event_data
            else:
                combined_data = pd.merge(combined_data, event_data,
                                         on=[self.year_col, 'PERIODO'], how='outer')
        table_frame = tk.Frame(tab_tabla)
        table_frame.pack_propagate(False)
        table_frame.pack(fill="both", expand=True)
        export_table = tk.Button(button_frame, text="Exportar a Excel", command=self.export_table(combined_data))
        export_table.pack(side=tk.LEFT)
        pt = Table(table_frame, dataframe=combined_data,
                   showtoolbar=True, showstatusbar=True,
                   width=self.right_panel.winfo_screenwidth()*2/3,
                   height=self.right_panel.winfo_screenheight()*2/3)
        pt.show()
        return tablas_por_evento

    def process_data(self):
        if self.data is not None and self.event_listbox is not None:
            if self.year_var.get() and self.week_var.get() and [
                    self.event_listbox.get(i)
                    for i in self.event_listbox.curselection()]:
                for widget in self.right_panel.winfo_children():
                    widget.destroy()
                self.setup_right_panel(skip=True)
    
    def cleanup(self):
        self.data = None
        self.event_listbox = None
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
    root.title("Metodologia Analisis de Comportamientos Inusuales MMWR")
    root.state('zoomed')
    app = DataTabsApp(root)

    def on_exit():
        app.cleanup()
        root.destroy()
        quit()

    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.mainloop()
