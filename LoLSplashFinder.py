import os
import subprocess
import configparser
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# App metadata
app_version = '0.1.0'
app_author = 'Huy Nguyen'
app_name = 'LoL Splash Finder'

# Define themes
dark_theme = {'bg_color': '#333333', 'fg_color': '#FFFFFF', 'hl_color': '#555555'}
light_theme = {'bg_color': '#FFFFFF', 'fg_color': '#000000', 'hl_color': '#DDDDDD'}
font_header = ('Helvetica', 13, 'bold')
font_body = ('Helvetica', 9)
font_about = ('Helvetica', 7)

# Check if tkinter & Pillow are available, exit if not
try:
    import tkinter as tk
    from PIL import Image, ImageTk
except ImportError as e:
    if "tkinter" in str(e):
        print('Error: Required package "python3-tk" not found. Please check your Python installation and reinstall if needed.')
    if "PIL" in str(e):
        print('Error: Required package "Pillow" not found. Please install it manually.')
    exit()


# Define constants for configuration keys
CONFIG_PATHS = 'Paths'
CONFIG_SETTINGS = 'Settings'
CONFIG_LOL_PATH = 'LoL'
CONFIG_APP_THEME = 'AppTheme'
CONFIG_SHOW_PLACEHOLDER = 'ShowPlaceholderSkin'
CONFIG_REVERSE_ORDER = 'ReverseDisplayOrder'


# Class to represent a skin entry
class SkinEntry:
    def __init__(self, folder, thumb_path):
        self.folder = folder
        self.thumb_path = thumb_path


# Class to handle tooltips
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.timer_id = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y += self.widget.winfo_rooty() + self.widget.winfo_height() - 21

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text, background=dark_theme['hl_color'], foreground=dark_theme['fg_color'], relief="solid", borderwidth=0)
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


# Function to load configuration settings
def load_config():
    config_file_path = 'config.ini'

    if not os.path.isfile(config_file_path):
        default_config = {
            CONFIG_PATHS: {CONFIG_LOL_PATH: 'Replace with your own path'},
            CONFIG_SETTINGS: {CONFIG_APP_THEME: 'dark', CONFIG_SHOW_PLACEHOLDER: 'False', CONFIG_REVERSE_ORDER: 'True'}
        }
        config = configparser.ConfigParser()
        config.update(default_config)

        with open(config_file_path, 'w') as configfile:
            configfile.write('# If your LoL workspace is not at the default location, set the correct path to the "Character" folder here (without the "\\" at the end).\n# You can change the app theme. Accepted values: "dark", "light"\n# You can unhide placeholder skins. A skin is considered a placeholder if its tile is smaller than 20 KB. Accepted values: "True", "False"\n\n')
            config.write(configfile)

    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config


# Function to find valid champions
def find_valid_champs(lol_path):
    return [champ_name for champ_name in os.listdir(lol_path) if os.path.exists(os.path.join(lol_path, champ_name, 'Skins', 'Base', 'Images'))
            and os.path.exists(os.path.join(lol_path, champ_name, 'Skins', 'Skin01', 'Images'))]


# Function to find valid skins for a given champion
def find_valid_skins(champ_name, lol_path):
    path = os.path.join(lol_path, champ_name, 'Skins')
    skin_folders_with_images = [folder for folder in os.listdir(path) if os.path.exists(os.path.join(path, folder, 'Images'))]

    config = load_config()
    show_placeholder = config[CONFIG_SETTINGS].getboolean(CONFIG_SHOW_PLACEHOLDER, fallback=False)
    reverse_display_order = config[CONFIG_SETTINGS].getboolean(CONFIG_REVERSE_ORDER, fallback=True)

    valid_skins = []

    for folder in sorted(skin_folders_with_images, key=lambda x: int(x[len('Skin'):] or 0), reverse=reverse_display_order):
        images_path = os.path.join(path, folder, 'Images')
        thumb_path = find_thumb(images_path)

        # Additional check for image file size if ShowPlaceholder is not set to true
        if show_placeholder or (thumb_path and os.path.getsize(thumb_path) > 20480):
            valid_skins.append(SkinEntry(folder, thumb_path))

    return valid_skins


# Function to find thumbnail for a skin
def find_thumb(images_path):
    thumb_files = [file for file in os.listdir(images_path) if '_tile_' in file.lower() and file.lower().endswith(('.jpg', '.jpeg'))]
    return os.path.join(images_path, thumb_files[0]) if thumb_files else None


# Function to open File Explorer at the selected skin's folder
def open_in_explorer(selected_champ, selected_skin, lol_path):
    path = os.path.join(lol_path, selected_champ, 'Skins', selected_skin, 'Images')
    subprocess.Popen(['explorer', path], shell=True)
    print(f'Opening File Explorer at: {path}')


# Event handler for champion selection
def on_champ_selected(event):
    selected_champ = champ_combobox.get()
    skin_entries = find_valid_skins(selected_champ, lol_path)
    update_skin_list(skin_entries)


# Event handler for skin selection
def on_skin_selected(event):
    selected_skin = event.widget.skin_entry.folder
    selected_champ = champ_combobox.get()
    open_in_explorer(selected_champ, selected_skin, lol_path)


# Function to update the skin list in the GUI
def update_skin_list(skin_entries):
    for widget in canvas.winfo_children():
        widget.destroy()

    photo_references = []

    for i, entry in enumerate(skin_entries):
        thumb_path = entry.thumb_path
        thumb = Image.open(thumb_path).resize((80, 80))
        photo = ImageTk.PhotoImage(thumb)
        photo_references.append(photo)

        row, col = i // 4, i % 4
        label = tk.Label(canvas, image=photo, bg=theme_colors['bg_color'])
        label.grid(row=row, column=col, padx=4, pady=4)
        label.bind('<Double-Button-1>', on_skin_selected)
        label.skin_entry = entry

        tooltip_text = entry.folder
        ToolTip(label, tooltip_text)

    canvas.photo_references = photo_references
    root.update_idletasks()
    root.geometry(f'390x{max(root.winfo_reqheight(), 545)}')


# Load configuration settings
config = load_config()
lol_path = config[CONFIG_PATHS][CONFIG_LOL_PATH]
app_theme = config[CONFIG_SETTINGS][CONFIG_APP_THEME]
show_placeholder = config[CONFIG_SETTINGS].getboolean(CONFIG_SHOW_PLACEHOLDER, fallback=False)
reverse_display_order = config[CONFIG_SETTINGS].getboolean(CONFIG_REVERSE_ORDER, fallback=True)

# Create main GUI window
root = tk.Tk()
root.title(f'{app_name} - v{app_version}')
root.resizable(False, False)

# Apply theme to the root window
theme_colors = dark_theme if app_theme == 'dark' else light_theme
root.config(bg=theme_colors['bg_color'])
root.geometry('390x545')

# Create and configure the champion selection combobox
champ_combobox = ttk.Combobox(root, values=find_valid_champs(lol_path), state='readonly', font=font_header, foreground=theme_colors['fg_color'])
champ_combobox.set('Select a Champion')
champ_combobox.grid(row=0, column=0, padx=15, pady=10, sticky='ew')
champ_combobox.config(width=37, style=f"{app_theme}.TCombobox")
champ_combobox.bind('<<ComboboxSelected>>', on_champ_selected)

# Create and configure the tip label
tip = tk.Label(root, text='Double-click to open a splash folder.', font=font_body, bg=theme_colors['bg_color'], fg=theme_colors['fg_color'])
tip.grid(row=1, column=0, padx=12, pady=0, sticky='w')

# Create and configure the about label
about = tk.Label(root, text=f'v{app_version} by {app_author}', font=font_about, fg='grey', bg=theme_colors['bg_color'])
about.grid(row=1, column=0, padx=11, pady=0, sticky='se')

# Create and configure the canvas for displaying skin thumbnails
canvas = tk.Frame(root, bg=theme_colors['bg_color'])
canvas.grid(row=2, column=0, padx=10, pady=5, sticky='nsew')

# Apply theme to ttk.Combobox
style = ttk.Style()
style.theme_create("dark", parent="alt", settings={
    "TCombobox": {"configure": {"padding": 5, "background": theme_colors['bg_color'], "fieldbackground": theme_colors['bg_color'], "selectbackground": theme_colors['bg_color'], "foreground": theme_colors['fg_color'], "selectforeground": theme_colors['fg_color']}},
    "TCombobox.Popup": {"configure": {"padding": 5, "background": theme_colors['hl_color'], "selectforeground": theme_colors['fg_color']}}}
    )
style.theme_create("light", parent="alt", settings={
    "TCombobox": {"configure": {"padding": 5, "background": theme_colors['bg_color'], "fieldbackground": theme_colors['bg_color'], "selectbackground": theme_colors['bg_color'], "foreground": theme_colors['fg_color'], "selectforeground": theme_colors['fg_color']}},
    "TCombobox.Popup": {"configure": {"padding": 5, "background": theme_colors['hl_color'], "selectforeground": theme_colors['fg_color']}}}
    )
style.theme_use(app_theme)

# Start the GUI event loop
root.mainloop()
