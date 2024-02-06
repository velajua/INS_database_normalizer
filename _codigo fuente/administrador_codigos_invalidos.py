
import re
import tkinter as tk

from tkinter import ttk
from tkinter import messagebox, Scrollbar

from PIL import Image, ImageDraw, ImageTk
from unidecode import unidecode


def create_image():
    image = Image.new('RGB', (18, 18), color='white')
    draw = ImageDraw.Draw(image)
    draw.text((-1, -1), 'A', fill='black')
    draw.text((5, -1), 'D', fill='blue')
    draw.text((11, -1), 'N', fill='green')
    draw.text((-1, 8), 'C', fill='black')
    draw.text((5, 8), 'O', fill='blue')
    draw.text((11, 8), 'D', fill='green')
    return ImageTk.PhotoImage(image)

# Load codes from file
def load_codes():
    global codes
    try:
        from codigos_invalidos import CODS_INV
        codes = CODS_INV[:]
    except ImportError:
        messagebox.showerror(
            "Error", "Archivo 'codigos_invalidos.py' No ha sido encontrado o tiene un error en el formato.")
        codes = []
    update_listbox()

# Update the listbox with current codes
def update_listbox():
    codes_listbox.delete(0, tk.END)
    for code in codes:
        codes_listbox.insert(tk.END, code)


def add_code():
    new_code = unidecode(code_entry.get().strip().upper()).replace('"', '').replace("'", '')  # Make input uppercase
    # Check if the code is exactly 5 characters long and contains only letters and numbers
    if len(new_code) != 5 or not re.match('^[A-Z0-9]{5}$', new_code):
        # If it doesn't meet the conditions, show an error in a top-level window
        error_window = tk.Toplevel(root)
        error_window.title("Error")
        error_window.geometry("300x100")
        tk.Label(error_window, text="El codigo debe de tener 5 caracteres alfanumericos.").pack(pady=20)
        tk.Button(error_window, text="OK", command=error_window.destroy).pack()
        return  # Stop the function so nothing else happens

    if new_code and new_code not in codes:
        codes.append(new_code)
        update_listbox()
        code_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Advertencia", "El codigo esta vacio o ya existe.")


# Remove selected code
def remove_code():
    selection = codes_listbox.curselection()
    if selection:
        codes.pop(selection[0])
        update_listbox()

# Update the file with current codes
def update_file():
    with open('codigos_invalidos.py', 'w') as file:
        file.write("CODS_INV = [\n")
        for code in sorted(list(set(codes))):
            file.write(f"'{code}',\n")
        file.write("]")
    messagebox.showinfo("Exito", "El archivo ha sido actualizado correctamente.")



def verify_code():
    # Get the code from the entry widget and convert it to uppercase
    code_to_verify = code_entry.get().upper()
    
    # Validate the code format
    if not re.match('^[A-Z0-9]{5}$', code_to_verify):
        # If the code doesn't meet the criteria, show an error message
        messagebox.showerror("Codigo Invalido",
                             "El codigo debe de tener 5 caracteres alfanumericos.")
        return  # Exit the function to prevent further execution

    # Create a top-level window for displaying the verification result
    verify_window = tk.Toplevel(root)
    verify_window.title(f"Verificar Codigo: {code_to_verify}")
    verify_window.geometry("300x100")  # Adjust the size as needed
    
    # Check if the code is in the list
    if code_to_verify in codes:
        message = f"El codigo: {code_to_verify}, SI se encuntra en la lista."
    else:
        message = f"El codigo: {code_to_verify}, NO se encuentra en la lista."
    
    # Display the message in the top-level window
    tk.Label(verify_window, text=message).pack(pady=20)
    # Add a button to close the window
    tk.Button(verify_window, text="OK", command=verify_window.destroy).pack()


if __name__ == '__main__':
    # Create the main window
    root = tk.Tk()
    icon_image = create_image()
    # Set the image as the app's icon
    root.iconphoto(True, icon_image)
    root.title("Administrar Codigos Invalidos")

    # Create a frame for the listbox and scrollbar
    listbox_frame = tk.Frame(root)
    listbox_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Listbox to display codes
    codes_listbox = tk.Listbox(listbox_frame, height=15)
    codes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Scrollbar
    scrollbar = Scrollbar(listbox_frame, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the listbox to scroll with the scrollbar
    codes_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=codes_listbox.yview)

    # Entry to add new codes
    code_entry = tk.Entry(root)
    code_entry.pack(padx=10, pady=5, fill=tk.X)

    # Action buttons frame
    action_frame = tk.Frame(root)
    action_frame.pack(padx=10, pady=10)

    # Add, Verify, Remove buttons in the action frame
    add_button = tk.Button(action_frame, text="Añadir Codigo", command=add_code)
    add_button.pack(side=tk.LEFT, padx=5, pady=5)

    verify_button = tk.Button(action_frame, text="Verificar Codigo", command=verify_code)
    verify_button.pack(side=tk.LEFT, padx=5, pady=5)

    remove_button = tk.Button(action_frame, text="Quitar Codigo", command=remove_code)
    remove_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Separator
    separator = ttk.Separator(root, orient='horizontal')
    separator.pack(fill='x', padx=5, pady=5)

    # Update file button
    update_file_button = tk.Button(root, text="Actualizar Archivo", command=update_file)
    update_file_button.pack(pady=10)

    codes = []
    load_codes()
    root.geometry(f"350x{min(800, len(codes)*16)+180}")


    root.mainloop()

