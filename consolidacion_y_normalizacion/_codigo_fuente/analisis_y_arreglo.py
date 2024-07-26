import os
import re
import json
import hashlib
import difflib
import pandas as pd
import tkinter as tk

import logging
import traceback

from uuid import uuid4
from unidecode import unidecode

from tkinter import ttk, filedialog

from typing import List, Union, Tuple
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageTk

logging.basicConfig(filename='error_log.log', level=logging.ERROR)


def open_popup(message):
    popup = tk.Toplevel()
    popup.title("Message")
    # Set the position of the popup
    popup.geometry("300x150")
    # Add a label with the message
    message_label = tk.Label(popup, text=message, wraplength=280)
    message_label.pack(pady=20)
    # Add a button to close the popup
    close_button = tk.Button(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=5)
    # Wait until the popup window is closed
    popup.wait_window()


ERR_COLS, CDM, CODS_INV, MAPPER, CDM_ACC = None, None, None, None, None

enc = 'latin-1'

try:
    with open(os.path.join('config_analisis', 'errores_cols_salida.json'), 'r', encoding=enc) as file:
        data = json.load(file)
        ERR_COLS = data.get("ERR_COLS", [])  # Provide a default empty list in case the key doesn't exist
except FileNotFoundError:
    open_popup(f"Error: The file '{os.path.join('config_analisis', 'errores_cols_salida.json')}' was not found.")
    ERR_COLS = []
    exit()
except json.JSONDecodeError:
    open_popup(f"Error: There was an issue decoding '{os.path.join('config_analisis', 'errores_cols_salida.json')}'.")
    ERR_COLS = []
    exit()
except Exception as e:
    open_popup(f"An unexpected error occurred: {str(e)}")
    ERR_COLS = []
    exit()

try:
    with open(os.path.join('config_analisis', 'diccionario_codigos.json'), 'r', encoding=enc) as file:
        data = json.load(file)
        CDM = data.get("COD_DEPT_MUN", {})  # Provide a default empty dict in case the key doesn't exist
except FileNotFoundError:
    open_popup(f"Error: The file '{os.path.join('config_analisis', 'diccionario_codigos.json')}' was not found.")
    CDM = {}
    exit()
except json.JSONDecodeError:
    open_popup(f"Error: There was an issue decoding '{os.path.join('config_analisis', 'diccionario_codigos.json')}'.")
    CDM = {}
    exit()
except Exception as e:
    open_popup(f"An unexpected error occurred: {str(e)}")
    CDM = {}
    exit()

try:
    with open(os.path.join('config_analisis', 'diccionario_codigos_acc.json'), 'r', encoding=enc) as file:
        data = json.load(file)
        CDM_ACC = data.get("COD_DEPT_MUN_ACC", {})  # Provide a default empty dict in case the key doesn't exist
except FileNotFoundError:
    open_popup(f"Error: The file '{os.path.join('config_analisis', 'diccionario_codigos_acc.json')}' was not found.")
    CDM_ACC = {}
    exit()
except json.JSONDecodeError:
    open_popup(f"Error: There was an issue decoding '{os.path.join('config_analisis', 'diccionario_codigos_acc.json')}'.")
    CDM_ACC = {}
    exit()
except Exception as e:
    open_popup(f"An unexpected error occurred: {str(e)}")
    CDM_ACC = {}
    exit()

try:
    with open(os.path.join('config_analisis', 'codigos_invalidos.json'), 'r', encoding=enc) as file:
        data = json.load(file)
        CODS_INV = data.get("CODS_INV", [])  # Provide a default empty list in case the key doesn't exist
except FileNotFoundError:
    open_popup(f"Error: The file '{os.path.join('config_analisis', 'codigos_invalidos.json')}' was not found.")
    CODS_INV = []
    exit()
except json.JSONDecodeError:
    open_popup(f"Error: There was an issue decoding '{os.path.join('config_analisis', 'codigos_invalidos.json')}'.")
    CODS_INV = []
    exit()
except Exception as e:
    open_popup(f"An unexpected error occurred: {str(e)}")
    CODS_INV = []
    exit()

try:
    with open(os.path.join('config_analisis', 'mapeo_nombres.json'), 'r', encoding=enc) as file:
        data = json.load(file)
        MAPPER = data.get("MAPPER", {})  # Provide a default empty dict in case the key doesn't exist
except FileNotFoundError:
    open_popup(f"Error: The file '{os.path.join('config_analisis', 'mapeo_nombres.json')}' was not found.")
    MAPPER = {}
    exit()
except json.JSONDecodeError:
    open_popup(f"Error: There was an issue decoding '{os.path.join('config_analisis', 'mapeo_nombres.json')}'.")
    MAPPER = {}
    exit()
except Exception as e:
    open_popup(f"An unexpected error occurred: {str(e)}")
    MAPPER = {}
    exit()

dept_mapper = MAPPER['DEPTO']
mun_mapper = MAPPER['MUN']
both_mapper = MAPPER['BOTH']

values_ = list(CDM.values())
values_ = [re.sub(r'\([^\)]*\)', '', i) for i in values_]

global err_df, err_df_2, df, file_name, file_order, progress_bar, root

progress_bar = None
df = pd.DataFrame()
err_df = pd.DataFrame()
err_df_2 = pd.DataFrame()


def create_image():
    image = Image.new('RGB', (18, 18), color='white')
    draw = ImageDraw.Draw(image)
    draw.text((0, -1), 'A', fill='black')
    draw.text((6, -1), 'L', fill='blue')
    draw.text((12, -1), 'S', fill='green')
    draw.text((0, 8), 'D', fill='black')
    draw.text((6, 8), 'T', fill='blue')
    draw.text((12, 8), 'S', fill='green')
    return ImageTk.PhotoImage(image)


def search_file(label_):
    def cargar_Archivo():
        global file_name, file_order
        # Determine the initial directory based on label_
        initial_dir = './' if label_ == 'base' else './config_analisis'
        filetypes = [('Excel files', '*.xls *.xlsx'), ('CSV files', '*.csv')] if label_ == 'base' else [('Text files', '*.txt')]
        # Open a file dialog with the initial directory set
        filepath = filedialog.askopenfilename(initialdir=initial_dir, filetypes=filetypes)
        if filepath:  # Check if a file was selected
            # Extract the file name from the full path
            filename = os.path.basename(filepath)
            # Update the appropriate string variable based on label_
            file_name.set(filename) if label_ == 'base' else file_order.set(filename)
        else:
            file_name.set('') if label_ == 'base' else file_order.set('')
    return cargar_Archivo


def excel_num_to_date(excel_date_num):
    if excel_date_num >= 61:
        excel_date_num -= 1

    excel_base_date = datetime(1899, 12, 31)
    python_date = excel_base_date + timedelta(days=excel_date_num)
    return python_date


def apply_excel_date(fecha):
    try:
        date_obj = datetime.strptime(fecha, '%d/%m/%Y')
        fecha = date_obj.strftime('%Y-%m-%d')
    except:
        try:
            date_obj = datetime.strptime(fecha, '%d %b %Y %H:%M:%S:%f')
            fecha = date_obj.strftime('%d %b %Y %H:%M:%S:%f')[:-3]
        except:
            if str(fecha)[:2] not in ['19', '20'] and str(
                    fecha)[0].isnumeric():
                if len(str(fecha).split('/')) == 3 or len(
                        str(fecha).split('-')) == 3 or str(
                            fecha)[:3] == '00:':
                    return fecha
                fecha = str((excel_num_to_date(int(fecha))))            
    return fecha


def get_clean_code(x, info):
    cod_dept = None
    cod_mun = None
    # Split the info string into pairs and iterate through them
    for pair in info.split(';'):
        # Remove parentheses and split into individual column names
        temp1, temp2 = pair.strip('()').split(',')
        # Check if both values in the pair exist and are not 'nan'
        try:
            if not cod_dept or str(cod_dept).lower() in ['nan', 'none']:
                cod_dept = x[temp1]
            if not cod_mun or str(cod_mun).lower() in ['nan', 'none']:
                cod_mun = x[temp2]
        except:
            open_popup(f'Error en columnas {temp1}, {temp2} para orden "cod"')
            quit()
    cod_dept = str(cod_dept).lower()
    cod_mun = str(cod_mun).lower()
    if len(cod_mun) >= 5:
        cod_dept = cod_mun
    elif len(cod_mun) == 4:
            cod_dept = cod_mun.zfill(5)
    else:
        cod_dept = cod_dept.zfill(2) if len(
            cod_dept) != 2 else cod_dept
        cod_mun = cod_mun.zfill(3) if len(
            cod_mun) != 3 else cod_mun
        cod_dept = cod_dept + cod_mun
    if cod_dept.lower() == 'nannan' or cod_dept in CODS_INV:
        cod_dept = '0'
    if cod_dept[-3:].lower() == 'nan':
        cod_dept = cod_dept[:2] + '000'
    if len(cod_dept) == 6:
        cod_dept = cod_dept[-2:] + cod_dept[:3]
    if cod_dept in CODS_INV:
        cod_dept = '0'
    return cod_dept


def get_joined_code(x, info, cols_out):
    cod_dept = None
    cod_mun = None
    # Split the info string into pairs and iterate through them
    for pair in info.split(';'):
        # Remove parentheses and split into individual column names
        temp1, temp2 = pair.strip('()').split(',')
        # Check if both values in the pair exist and are not 'nan'
        try:
            if not cod_dept or str(cod_dept).lower() in ['nan', 'none']:
                cod_dept = x[temp1]
            if not cod_mun or str(cod_mun).lower() in ['nan', 'none']:
                cod_mun = x[temp2]
        except:
            open_popup(f'Error en columnas {temp1}, {temp2} para orden "name_cod"')
            quit()
    dept_ = unidecode(str(cod_dept)).upper().strip()
    mun_ = unidecode(str(cod_mun)).upper().strip()
    dept_ = re.sub(r'\s*\([^\)]*\)', '', dept_)
    mun_ = re.sub(r'\s*\([^\)]*\)', '', mun_)
    dept_ = dept_mapper[dept_] if dept_ in dept_mapper else dept_
    mun_ = mun_mapper[mun_] if mun_ in mun_mapper else mun_
    mun_ = both_mapper[dept_ + ' ' + mun_] if (
        dept_ + ' ' + mun_) in both_mapper else mun_

    if dept_ in ['NAN', 'DESCONOCIDO'] and mun_ in ['NAN', 'DESCONOCIDO'] and str(x[cols_out]) == '0':
        x[cols_out] = '00000'
    elif dept_ != 'NAN' and mun_ == 'NAN' and str(x[cols_out]) == '0':
        mun_ = f'* {dept_}. MUNICIPIO DESCONOCIDO'
    if str(x[cols_out]) == '0':
        joined_str = dept_ + '%' + mun_
        for code, name in CDM.items():
            if joined_str == name:
                x[cols_out] = code
                break
            else:
                pass
    return x


def find_str(x, info, temp_col):
    cod_dept = None
    cod_mun = None
    # Split the info string into pairs and iterate through them
    for pair in info.split(';'):
        # Remove parentheses and split into individual column names
        temp1, temp2 = pair.strip('()').split(',')
        # Check if both values in the pair exist and are not 'nan'
        try:
            if not cod_dept or str(cod_dept).lower() in ['nan', 'none']:
                cod_dept = str(x[temp1].values[0])
            if not cod_mun or str(cod_mun).lower() in ['nan', 'none']:
                cod_mun = str(x[temp2].values[0])
        except:
            open_popup(f'Error en columnas {temp1}, {temp2} para orden "name_cod" de archivo auxiliar')
            quit()
    cod_d_m = cod_dept + '%' + cod_mun
    cod_d_m = unidecode(str(cod_d_m)).upper().strip()
    for code, name in CDM.items():
        if cod_d_m == name:
            x[temp_col] = code
            return x
    temp = category_mapper(values_, [re.sub(r'\([^\)]*\)', '', cod_d_m)], 'ans')
    if temp:
        for code, name in zip(CDM.keys(), values_):
            if temp[0] == name:
                x[temp_col] = code
                return x
    return x


def try_to_parse(x, cols_in, DICT, action):
    try:
        x = str(x).upper()
        out = DICT[x].split('%')
        return out
    except KeyError as e:
        global err_df_2, df
        key_error_string = str(e).strip("'")

        bad_row = df.loc[df[cols_in] == key_error_string][[
            i for i in ERR_COLS if i in df.columns]]
        bad_row['REASON'] = action
        err_df_2 = pd.concat([err_df_2, bad_row], ignore_index=True)
        return ['0', '0']


def category_mapper(master_list: List[str],
                    list_to_map: List[str],
                    type_: str = 'both') -> Union[
                        Tuple[List[str], List[str]], List[str]]:
    assert type_ in ['both', 'ans', 'filled'
                     ], f'Invalid value for type_: {type_}'
    ans, filled = [], []
    for i in list_to_map:
        match = difflib.get_close_matches(i, master_list)
        ans.append(match[0] if match else '')
        filled.append(match[0] if match else i)
    if type_ == 'both':
        return ans, filled
    elif type_ == 'ans':
        return ans
    elif type_ == 'filled':
        return filled


def transform_value(val):
        val = unidecode(str(val)).upper().strip()
        val = re.sub(r'\s*\([^\)]*\)', '', val)
        return val


def mask_half_of_each_word(name):
    words = str(name).replace('  ', ' ').strip().split()
    masked_words = []
    for word in words:
        half_length = len(word) // 2
        masked_word = word[:half_length] + '*' * (len(word) - half_length)
        masked_words.append(masked_word)
    return ' '.join(masked_words)


def column_contains(value, column):
    if re.search(value, str(column), re.IGNORECASE):
        return 1
    return 2


def get_first_non_null(row, valid_cols):
        for col in valid_cols:
            if pd.notnull(row[col]):
                return col
        return None


def analyzer():
    try:
        global err_df, err_df_2, df, file_name, file_order, progress_bar, root
        progress_bar = ttk.Progressbar(root,
                                    orient='horizontal',
                                    length=350,
                                    mode="determinate")
        progress_bar.pack(pady=20)
        progress_bar["value"] = 0
        root.update()
        if not file_name.get() and file_order.get():
            open_popup('Debe Seleccionar Archivos para Analizar')
            progress_bar.destroy()
            root.update()
            return
        if '.csv' in (file_name := file_name.get()):
            df = pd.read_csv(file_name, sep=';',
                            dtype='str', encoding=enc)
        elif '.xlsx' in file_name:
            df = pd.read_excel(file_name, dtype=str)
        progress_bar["value"] = 10
        root.update()
        with open(os.path.join('config_analisis',
                            file_order.get()), 'r', encoding='utf-8') as f:
            actions = [i.strip() for i in f.readlines() if i]
        progress_bar["value"] = 20
        root.update()

        for index_, action in enumerate(actions):
            print(f'current action: {action}')
            if len(action.split()) == 3:
                order, cols_in, cols_out = action.split()
                if order == 'f':
                    if cols_in in df.columns:
                        df[cols_out] = df[cols_in].apply(
                            lambda x: apply_excel_date(x)
                            if x and str(x).lower() not in [
                                'nan', 'none']
                            else x)
                    else:
                        open_popup(f'Error en columnas {cols_in} para orden "f"')
                        quit()
                elif order == 'cod':
                    df[cols_out] = df.apply(lambda x:
                                            get_clean_code(x, cols_in),
                                            axis=1)
                elif order == 'name_cod':
                    if cols_out not in df.columns:
                        df[cols_out] = '0'
                    df = df.apply(lambda x: get_joined_code(x, cols_in, cols_out)
                                if len(str(x[cols_out])) == 1 else x, axis=1)
                    filtered_df = df.loc[df[cols_out].apply(
                        lambda x: len(str(x)) == 1)][[i for i in ERR_COLS if i in df.columns]].drop_duplicates()
                    filtered_df['REASON'] = action
                    err_df = pd.concat([err_df, filtered_df], ignore_index=True)
                elif order == 'mask':
                    if not cols_in in df.columns:
                        open_popup(f'Error en columnas {cols_out} o {cols_in} para orden "mask"')
                        quit()
                    df[cols_out] = df[cols_in].apply(lambda x: mask_half_of_each_word(x))
                elif order == 'contains':
                    values = cols_in.split(',')
                    if len(values) != 2 or not values[0] in df.columns:
                        open_popup(f'Error en columnas {cols_out} o {cols_in} para orden "contains"')
                        quit()
                    col, word = values
                    df[cols_out] = df[col].apply(lambda x: column_contains(word, x))
                elif order ==  'diff_val':
                    cols_in = cols_in.split(',')
                    for col in cols_in:
                        if col not in df.columns:
                            open_popup(f'Error en columnas {cols_in} para orden "diff_val"')
                            quit()
                    df[cols_out] = df.apply(lambda row: ''.join(str(row[col]).replace(' ', '').replace('*', '')[-4:] for col in cols_in), axis=1)
                elif order ==  'hash':
                    cols_in = cols_in.split(',')
                    for col in cols_in:
                        if col not in df.columns:
                            open_popup(f'Error en columnas {cols_in} para orden "hash"')
                            quit()
                    df[cols_out] = df.apply(lambda row: hashlib.sha256(''.join(str(row[col]) for col in cols_in).encode()).hexdigest()[:16], axis=1)
                elif order == 'cod_name':
                    cols_out = cols_out.split(',')
                    if len(cols_out) != 2 or not cols_in in df.columns:
                        open_popup(f'Error en columnas {cols_out} o {cols_in} para orden "cod_name"')
                        quit()
                    df[cols_out] = df[cols_in].apply(lambda x: try_to_parse(
                        x, cols_in, CDM, action)).to_list()
                elif order == 'cod_name_acc':
                    cols_out = cols_out.split(',')
                    if len(cols_out) != 2 or not cols_in in df.columns:
                        open_popup(f'Error en columnas {cols_out} o {cols_in} para orden "cod_name"')
                        quit()
                    df[cols_out] = df[cols_in].apply(lambda x: try_to_parse(
                        x, cols_in, CDM_ACC, action)).to_list()
                    for col_ in cols_out:
                        df[col_] = df[col_].apply(lambda x: x.encode('latin-1').decode('utf-8'))
                elif order == '+':
                    col_names = cols_in.split(',')
                    if not all(y in df.columns for y in col_names):
                        open_popup(f'Error en columnas {cols_in} para orden "+"')
                        # quit()
                    df[cols_out] = df[col_names].apply(
                        lambda x: ''.join(x.astype(str)), axis=1)
                elif order == '-':
                    if not cols_in in df.columns or not cols_out in df.columns or cols_in != cols_out:
                        open_popup(f'Error en columnas {cols_in} para orden "-"')
                        quit()
                    df = df.drop(columns=[cols_in])
                elif order == 'ag':
                    cols_part, word = cols_in.split(';')
                    cols = cols_part.strip('()').split(',')
                    print(cols_part, word, cols)
                    if all(col not in df.columns for col in cols) and word == '':
                        for col_out in cols_out:
                            df[col_out] = word
                    else:
                        get_first_non_null_col = lambda row: next((row[col] for col in cols if col in df.columns and pd.notnull(row[col])), word)
                        df[cols_out] = df.apply(get_first_non_null_col, axis=1)
                elif order == 'f0':
                    cols, zfill_width = cols_in.split(';')
                    zfill_width = int(zfill_width)
                    if not cols in df.columns:
                        open_popup(f'Error en columnas {cols_in} para orden "f0"')
                        quit()
                    df[cols_out] = df[cols].astype(str).str.zfill(zfill_width)
                elif order == 'cut':
                    cols, _index, _length = cols_in.split(';')
                    if not cols in df.columns or not _index in ['start', 'end'] or not _length.isnumeric():
                        open_popup(f'Error en columnas {cols_in} para orden "cut"')
                        quit()
                    if _index == 'start':
                        df[cols_out] = df[cols].apply(lambda x: str(x)[:int(_length)])
                    elif _index == 'end':
                        df[cols_out] = df[cols].apply(lambda x: str(x)[-1*int(_length):])
                elif order == 'if':
                    expr, true_, false_ = cols_in.split(';')
                    cols, val = expr.split('=')
                    if not cols in df.columns:
                        open_popup(f'Error en columnas {cols_in} para orden "if"')
                        quit()
                    df[cols_out] = df[cols].apply(lambda x: true_ if str(x) == val else false_)
                elif order == '=':
                    df[cols_out] = cols_in
                elif order[0] == '&':
                    order = order[1:]
                    order = order.split('&')
                    if len(order) != 3:
                        open_popup(f'Error en orden {order} para orden "&"')
                        quit()
                    file, out_cols, operation = order
                    out_cols = out_cols.split(',')
                    if not os.path.exists(os.path.join('config_analisis', file)):
                        open_popup(f'Error en archivo {file} para orden "&"')
                        quit()
                    else:
                        temp_col = str(uuid4())
                        temp_file = pd.read_excel(os.path.join('config_analisis', file))
                        temp_file.columns = [
                            unidecode(str(col)).upper().replace(' ', '_').strip('_').strip()
                            for col in temp_file.columns]
                        if not all(y in temp_file.columns for y in out_cols):
                            open_popup(f'Error en columnas {out_cols} para orden "&"')
                            quit()
                        if not cols_out in df.columns:
                            open_popup(f'Error en columnas {cols_out} para orden "&"')
                            quit()
                        if operation == 'name_cod':
                            temp_file[temp_col] = None
                            temp_file = temp_file.apply(lambda x: find_str(x, cols_in, temp_col), axis=1)
                            temp_file = temp_file[out_cols + [temp_col]]
                            df = df.merge(temp_file, left_on=cols_out, right_on=temp_col, how='left')
                            df = df.drop(columns=[temp_col])
            else:
                open_popup(f'Error en formato para {action}')
                quit()
            progress_bar["value"] = 20 + (50/len(actions) * index_)
            root.update()

        for col in err_df.columns:
            err_df[col] = err_df[col].apply(transform_value)

        err_df = err_df.drop_duplicates()

        for i in err_df_2.columns:
            err_df_2[i] = err_df_2[i].apply(
                lambda x: unidecode(str(x)).upper().strip())

        err_df_2 = err_df_2.drop_duplicates()

        progress_bar["value"] = 90
        root.update()
        if err_df.empty and err_df_2.empty:
            print('writing data to file')
            if '.csv' in file_name:
                df.to_csv(file_name, index=False, sep=';', encoding=enc)
            elif '.xls' in file_name:
                write_large_excel(df, file_name)
        else:
            print('writing errors to file')
            temp_df = pd.concat([err_df, err_df_2], ignore_index=True, sort=False)
            write_large_excel(temp_df, 'ERROR_' + file_name.replace('.csv', '') + '.xlsx')
        print('finished')
        progress_bar.destroy()
        root.update()
    except Exception:
        logging.error("Exception occurred", exc_info=True)
        logging.error(traceback.format_exc())
        progress_bar.destroy()
        root.update()
        open_popup(f'Se ha generado un log del error')


def write_large_excel(df, file_name, chunk_size=100000):
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        for start in range(0, len(df), chunk_size):
            end = start + chunk_size
            df[start:end].to_excel(writer, index=False, header=(start == 0), startrow=start)


if __name__ == '__main__':
    # Create the main window
    root = tk.Tk()
    icon_image = create_image()
    # Set the image as the app's icon
    root.iconphoto(True, icon_image)
    root.title("Analisis y Arreglo de Datos")
    root.geometry("400x375")  # Adjust size as needed

    # Initialize the string variable
    file_name = tk.StringVar(value="", master=root)
    file_order = tk.StringVar(value="", master=root)

    # Add a label that acts like a title
    title_label = tk.Label(root, text="Analisis y Arreglo de Datos", font=("Arial", 14))
    title_label.pack(pady=10)
    separator = ttk.Separator(root, orient='horizontal')
    separator.pack(fill='x', padx=5, pady=5)

    # Add a button to search for a file
    search_file_button = tk.Button(root, text="Archivo Base para Analizar", command=search_file('base'))
    search_file_button.pack(pady=10)

    # Add a label to display the file name, linked to the string variable
    file_name_label = tk.Label(root, textvariable=file_name, font=("Arial", 12))
    file_name_label.pack(pady=10)

    separator = ttk.Separator(root, orient='horizontal')
    separator.pack(fill='x', padx=5, pady=5)

    # Add a button to search for a file
    search_file_button = tk.Button(root, text="Archivo de Ordenes", command=search_file('order'))
    search_file_button.pack(pady=10)

    # Add a label to display the file name, linked to the string variable
    file_order_label = tk.Label(root, textvariable=file_order, font=("Arial", 12))
    file_order_label.pack(pady=10)

    separator = ttk.Separator(root, orient='horizontal')
    separator.pack(fill='x', padx=5, pady=5)

    analizer_button = tk.Button(root, text="Realizar Analisis", command=analyzer)
    analizer_button.pack(pady=10)

    # Start the Tkinter event loop
    root.mainloop()
