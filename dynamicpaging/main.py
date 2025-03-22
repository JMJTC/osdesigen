import tkinter as tk
from config.config_window import ConfigWindow


def main():
    root = tk.Tk()
    app = ConfigWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()