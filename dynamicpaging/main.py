import tkinter as tk
from config_window import ConfigWindow

def main():
    root = tk.Tk()
    config_window = ConfigWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()