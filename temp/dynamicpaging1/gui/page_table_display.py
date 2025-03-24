import tkinter as tk
from tkinter import ttk
from typing import List
from models.page_table import PageTableEntry

class PageTableDisplay:
    def __init__(self, parent: ttk.Frame, page_table: List[PageTableEntry]):
        self.frame = ttk.LabelFrame(parent, text="页表", padding="5")
        self.frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.page_table = page_table
        self.update_display()
    
    def update_display(self):
        # 清除现有显示
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # 创建表头
        headers = ["页号", "存在标志", "内存块号", "修改标志", "磁盘位置"]
        for i, header in enumerate(headers):
            ttk.Label(self.frame, text=header).grid(row=0, column=i, padx=5)
        
        # 显示页表内容
        for i, entry in enumerate(self.page_table):
            ttk.Label(self.frame, text=str(entry.page_number)).grid(
                row=i+1, column=0, padx=5)
            ttk.Label(self.frame, text="1" if entry.present else "0").grid(
                row=i+1, column=1, padx=5)
            ttk.Label(self.frame, text=str(entry.frame_number) if entry.present else "-").grid(
                row=i+1, column=2, padx=5)
            ttk.Label(self.frame, text="1" if entry.modified else "0").grid(
                row=i+1, column=3, padx=5)
            ttk.Label(self.frame, text=entry.disk_location).grid(
                row=i+1, column=4, padx=5) 