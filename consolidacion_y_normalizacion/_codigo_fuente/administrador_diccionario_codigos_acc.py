import re
import json
import tkinter as tk

from tkinter import Scrollbar, messagebox, simpledialog

from PIL import Image, ImageDraw, ImageTk

enc = 'latin-1'


def create_image():
    image = Image.new('RGB', (18, 18), color='white')
    draw = ImageDraw.Draw(image)
    draw.text((-1, -1), 'A', fill='black')
    draw.text((5, -1), 'D', fill='blue')
    draw.text((11, -1), 'N', fill='green')
    draw.text((-1, 8), 'D', fill='black')
    draw.text((5, 8), 'C', fill='blue')
    draw.text((11, 8), 'D', fill='green')
    return ImageTk.PhotoImage(image)


def load_codes():
    global codes_dict
    try:
        with open('diccionario_codigos_acc.json', 'r', encoding=enc) as file:
            data = json.load(file)
            codes_dict = data.get("COD_DEPT_MUN_ACC", {})
            codes_dict = {i.encode('latin-1').decode('utf-8'): j.encode('latin-1').decode('utf-8') for i, j in codes_dict.items()}
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo 'diccionario_codigos_acc.json'.\nDetalles: {str(e)}")
        codes_dict = {}
    update_listbox()


def sort_dict_alphabetically(input_dict):
    """Sorts a dictionary and all its nested dictionaries alphabetically by their keys."""
    sorted_dict = {}
    for key, value in sorted(input_dict.items()):
        if isinstance(value, dict):
            # If the value is a dictionary, sort it recursively
            sorted_dict[key] = sort_dict_alphabetically(value)
        else:
            sorted_dict[key] = value
    return sorted_dict


def update_file():
    try:
        # Ensure 'codes' is a set of unique codes, then sort them
        # Prepare the data in the format to be written to the JSON file
        data = {"COD_DEPT_MUN_ACC": sort_dict_alphabetically(
            {i.encode('utf-8').decode('latin-1'): j.encode('utf-8').decode('latin-1')
             for i, j in codes_dict.items()})}
        # Write the updated codes to the JSON file
        with open('diccionario_codigos_acc.json', 'w', encoding=enc) as file:
            json.dump(data, file, indent=4, ensure_ascii=False)  # Use indent for pretty-printing
        
        messagebox.showinfo("Éxito", "El archivo ha sido actualizado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Hubo un problema al actualizar el archivo.\nDetalles: {str(e)}")


def add_code():
    code = simpledialog.askstring("Nuevo Código", "Ingrese el código:")
    if code:
        code = code.strip().capitalize().replace('"', '').replace("'", '')
        if not code or not re.match('^[A-Z0-9]{5}$', code):
            messagebox.showerror("Error", "El código debe ser de 5 dígitos alfanuméricos.")
            return
        if code in codes_dict and not messagebox.askyesno(
                "Confirmar", f"El código {code} ya existe.\n\nDEPT: {codes_dict[code].split('%')[0]}\nMUN: {codes_dict[code].split('%')[1]}\n¿Desea sobrescribirlo?"):
            return
        depto = simpledialog.askstring("Nuevo Departamento", "Ingrese el Departamento:")
        if not depto:
            messagebox.showerror("Error", "Debe ingresar un Departamento.")
            return
        mun = simpledialog.askstring("Nuevo Municipio", "Ingrese el Municipio:")
        if not mun:
            messagebox.showerror("Error", "Debe ingresar un Municipio.")
            return
        temp_info = depto.strip().capitalize() + '%' + mun.strip().capitalize().replace('"', '').replace("'", '')
        for i, j in codes_dict.items():
            if temp_info == j and not messagebox.askyesno(
                    "Confirmar", f"El valor\nDEPT: {j.split('%')[0]}\nMUN: {j.split('%')[1]}\nExiste con codigo {i}\n¿Desea añadir el nuevo codigo?"):
                return
        codes_dict[code] = temp_info
        update_listbox()
    else:
        messagebox.showerror("Error", "Debe ingresar un código.")


def update_listbox():
    codes_listbox.delete(0, tk.END)
    for code, description in sorted(codes_dict.items()):
        codes_listbox.insert(tk.END, f"{code}:    {'    -    '.join(description.split('%'))}")


def remove_code():
    selection = codes_listbox.curselection()
    if not selection:
        messagebox.showwarning("Advertencia", "Seleccione un código para eliminar.")
        return
    code = codes_listbox.get(selection[0]).split(":", 1)[0]
    if messagebox.askyesno("Confirmar", f"¿Eliminar el código {code}?"):
        del codes_dict[code]
        update_listbox()


def verify_code():
    code = simpledialog.askstring("Verificar Código", "Ingrese el código a verificar:")
    if code in codes_dict:
        temp_data = codes_dict[code].split('%')
        messagebox.showinfo("Resultado", f"El código {code} existe:\n\nDEPT: {temp_data[0]}\nMUN: {temp_data[1]}")
    else:
        messagebox.showinfo("Resultado", f"El código {code} no existe.")


if __name__ == '__main__':
    # GUI setup
    root = tk.Tk()
    icon_image = create_image()
    # Set the image as the app's icon
    root.iconphoto(True, icon_image)
    root.title("Administrar Diccionario Codigos")
    root.geometry("700x450")

    action_frame = tk.Frame(root)
    action_frame.pack(padx=10, pady=10)

    add_button = tk.Button(action_frame, text="Añadir Codigo", command=add_code)
    add_button.grid(row=0, column=0, padx=5, pady=5)

    verify_button = tk.Button(action_frame, text="Verificar Codigo", command=verify_code)
    verify_button.grid(row=0, column=1, padx=5, pady=5)

    remove_button = tk.Button(action_frame, text="Quitar Codigo", command=remove_code)
    remove_button.grid(row=0, column=2, padx=5, pady=5)

    # Create a frame for the listbox and scrollbar
    listbox_frame = tk.Frame(root)
    listbox_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Listbox to display codes
    codes_listbox = tk.Listbox(listbox_frame, height=5)
    codes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Scrollbar
    scrollbar = Scrollbar(listbox_frame, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the listbox to scroll with the scrollbar
    codes_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=codes_listbox.yview)

    update_file_button = tk.Button(root, text="Actualizar Archivo", command=update_file)
    update_file_button.pack(pady=5)

    codes_dict = {}
    load_codes()

    root.mainloop()
