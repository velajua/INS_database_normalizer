import json
import tkinter as tk

from unidecode import unidecode
from tkinter import Scrollbar, messagebox

from PIL import Image, ImageDraw, ImageTk


def create_image():
    image = Image.new('RGB', (18, 18), color='white')
    draw = ImageDraw.Draw(image)
    draw.text((-1, -1), 'A', fill='black')
    draw.text((5, -1), 'D', fill='blue')
    draw.text((11, -1), 'N', fill='green')
    draw.text((-1, 8), 'M', fill='black')
    draw.text((5, 8), 'N', fill='blue')
    draw.text((11, 8), 'O', fill='green')
    return ImageTk.PhotoImage(image)


def load_mappings():
    global mapper
    try:
        with open('mapeo_nombres.json', 'r') as file:
            data = json.load(file)
            mapper = data.get("MAPPER", {})
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo 'mapeo_nombres.json'.\nDetalles: {str(e)}")
        mapper = {}
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
        data = {"MAPPER": sort_dict_alphabetically(mapper)}
        # Write the updated codes to the JSON file
        with open('mapeo_nombres.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)  # Use indent for pretty-printing
        
        messagebox.showinfo("Éxito", "El archivo ha sido actualizado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Hubo un problema al actualizar el archivo.\nDetalles: {str(e)}")


def add_mapping():
    mapping_type = mapping_type_var.get().upper()
    if mapping_type not in ['DEPTO', 'MUN', 'BOTH']:
        messagebox.showerror("Error", "Tipo de mapeo inválido.")
        return

    original = unidecode(original_entry.get().strip().upper()).replace('"', '').replace("'", '')
    mapped = unidecode(mapped_entry.get().strip().upper()).replace('"', '').replace("'", '')

    if not original or not mapped:
        messagebox.showerror("Error", "Original o Mapeo están vacíos.")
        return
    
    # Add to the mapper
    if original in mapper[mapping_type]:
        if messagebox.askyesno("Confirmar", "Este mapeo ya existe. ¿Actualizar?"):
            mapper[mapping_type][original] = mapped
    else:
        mapper[mapping_type][original] = mapped

    # Update the listbox display and clear entries
    update_listbox()
    original_entry.delete(0, tk.END)
    mapped_entry.delete(0, tk.END)


def update_listbox():
    mappings_listbox.delete(0, tk.END)
    for mapping_type, mappings in mapper.items():
        for original, mapped in mappings.items():
            mappings_listbox.insert(tk.END, f"{mapping_type}:    {original}    ->    {mapped}")


def remove_mapping():
    selection = mappings_listbox.curselection()
    if selection:
        selected_text = mappings_listbox.get(selection[0])
        mapping_type, rest = selected_text.split(":    ", 1)
        original, mapped = rest.split("    ->    ", 1)
        original = unidecode(original.strip().upper())
        if messagebox.askyesno("Confirmar", f"¿Eliminar el mapeo de {original}?"):
            del mapper[mapping_type][original]
            update_listbox()


def verify_mapping():
    original_to_verify = original_entry.get().strip().upper()
    mapping_type = mapping_type_var.get().upper()
    if original_to_verify in mapper[mapping_type]:
        messagebox.showinfo("Resultado", f"El mapeo para {original_to_verify} existe: {mapper[mapping_type][original_to_verify]}")
    else:
        messagebox.showinfo("Resultado", f"No se encontró el mapeo para {original_to_verify}.")


if __name__ == '__main__':
    # GUI setup
    root = tk.Tk()
    icon_image = create_image()
    # Set the image as the app's icon
    root.iconphoto(True, icon_image)
    root.title("Administrar Mapeo Nombres")
    root.geometry("700x450")

    input_frame = tk.Frame(root)
    input_frame.pack(padx=10, pady=10, fill=tk.X)

    radio_frame = tk.Frame(input_frame)
    radio_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    # Frame for entries
    entry_frame = tk.Frame(input_frame)
    entry_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10, expand=True)

    # Create and pack radio buttons in the radio frame
    mapping_type_var = tk.StringVar(value="DEPTO")
    tk.Radiobutton(radio_frame, text="DEPTO", variable=mapping_type_var, value="DEPTO").pack(anchor=tk.W)
    tk.Radiobutton(radio_frame, text="MUN", variable=mapping_type_var, value="MUN").pack(anchor=tk.W)
    tk.Radiobutton(radio_frame, text="BOTH", variable=mapping_type_var, value="BOTH").pack(anchor=tk.W)

    # Create and pack entries in the entry frame
    original_entry = tk.Entry(entry_frame)
    original_entry.pack(pady=5, fill=tk.X, expand=True)
    mapped_entry = tk.Entry(entry_frame)
    mapped_entry.pack(pady=5, fill=tk.X, expand=True)

    action_frame = tk.Frame(root)
    action_frame.pack(padx=10, pady=10)

    add_button = tk.Button(action_frame, text="Añadir Mapeo", command=add_mapping)
    add_button.grid(row=0, column=0, padx=5, pady=5)

    verify_button = tk.Button(action_frame, text="Verificar Mapeo", command=verify_mapping)
    verify_button.grid(row=0, column=1, padx=5, pady=5)

    remove_button = tk.Button(action_frame, text="Quitar Mapeo", command=remove_mapping)
    remove_button.grid(row=0, column=2, padx=5, pady=5)

    # Create a frame for the listbox and scrollbar
    listbox_frame = tk.Frame(root)
    listbox_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Listbox to display codes
    mappings_listbox = tk.Listbox(listbox_frame, height=5)
    mappings_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Scrollbar
    scrollbar = Scrollbar(listbox_frame, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the listbox to scroll with the scrollbar
    mappings_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=mappings_listbox.yview)

    update_file_button = tk.Button(root, text="Actualizar Archivo", command=update_file)
    update_file_button.pack(pady=5)

    mapper = {}
    load_mappings()

    root.mainloop()
