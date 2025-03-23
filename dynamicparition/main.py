import tkinter as tk
from memory_simulation import MemorySimulator

if __name__ == "__main__":
    root = tk.Tk()
    root.title("动态分区管理模拟器")
    root.geometry("800x600")  # 设置默认窗口大小
    app = MemorySimulator(root)
    root.mainloop()