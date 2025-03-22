import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable
from models.page_table import PageTableEntry

class PageTableSetup:
    def __init__(self, parent: ttk.Frame, on_save: Callable[[List[PageTableEntry]], None]):
        self.window = tk.Toplevel(parent)
        self.window.title("页表设置")
        self.window.geometry("800x600")
        self.on_save = on_save
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建页表显示区域
        self.tree = ttk.Treeview(main_frame, columns=("页号", "存在标志", "内存块号", "修改标志", "磁盘位置"),
                                show="headings")
        
        # 设置列标题
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 创建编辑区域
        edit_frame = ttk.LabelFrame(main_frame, text="编辑页表项", padding="5")
        edit_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 添加输入字段
        ttk.Label(edit_frame, text="页号:").grid(row=0, column=0, padx=5)
        self.page_entry = ttk.Entry(edit_frame, width=10)
        self.page_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(edit_frame, text="存在标志:").grid(row=0, column=2, padx=5)
        self.present_var = tk.BooleanVar()
        self.present_check = ttk.Checkbutton(edit_frame, variable=self.present_var)
        self.present_check.grid(row=0, column=3, padx=5)
        
        ttk.Label(edit_frame, text="内存块号:").grid(row=0, column=4, padx=5)
        self.frame_entry = ttk.Entry(edit_frame, width=10)
        self.frame_entry.grid(row=0, column=5, padx=5)
        
        ttk.Label(edit_frame, text="修改标志:").grid(row=0, column=6, padx=5)
        self.modified_var = tk.BooleanVar()
        self.modified_check = ttk.Checkbutton(edit_frame, variable=self.modified_var)
        self.modified_check.grid(row=0, column=7, padx=5)
        
        ttk.Label(edit_frame, text="磁盘位置:").grid(row=0, column=8, padx=5)
        self.disk_entry = ttk.Entry(edit_frame, width=10)
        self.disk_entry.grid(row=0, column=9, padx=5)
        
        # 添加按钮
        ttk.Button(edit_frame, text="添加", command=self._add_entry).grid(row=0, column=10, padx=5)
        ttk.Button(edit_frame, text="修改", command=self._modify_entry).grid(row=0, column=11, padx=5)
        ttk.Button(edit_frame, text="删除", command=self._delete_entry).grid(row=0, column=12, padx=5)
        
        # 保存按钮
        ttk.Button(main_frame, text="保存", command=self._save).grid(row=2, column=0, columnspan=3, pady=10)
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
    
    def _add_entry(self):
        try:
            page_number = int(self.page_entry.get())
            frame_number = int(self.frame_entry.get()) if self.present_var.get() else -1
            disk_location = self.disk_entry.get()
            
            self.tree.insert("", tk.END, values=(
                page_number,
                "1" if self.present_var.get() else "0",
                frame_number if self.present_var.get() else "-",
                "1" if self.modified_var.get() else "0",
                disk_location
            ))
            
            self._clear_entries()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def _modify_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要修改的项")
            return
        
        try:
            page_number = int(self.page_entry.get())
            frame_number = int(self.frame_entry.get()) if self.present_var.get() else -1
            disk_location = self.disk_entry.get()
            
            self.tree.item(selected[0], values=(
                page_number,
                "1" if self.present_var.get() else "0",
                frame_number if self.present_var.get() else "-",
                "1" if self.modified_var.get() else "0",
                disk_location
            ))
            
            self._clear_entries()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def _delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的项")
            return
        
        self.tree.delete(selected[0])
        self._clear_entries()
    
    def _on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        values = self.tree.item(selected[0])["values"]
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, values[0])
        
        self.present_var.set(values[1] == "1")
        self.frame_entry.delete(0, tk.END)
        self.frame_entry.insert(0, values[2] if values[2] != "-" else "")
        
        self.modified_var.set(values[3] == "1")
        self.disk_entry.delete(0, tk.END)
        self.disk_entry.insert(0, values[4])
    
    def _clear_entries(self):
        self.page_entry.delete(0, tk.END)
        self.present_var.set(False)
        self.frame_entry.delete(0, tk.END)
        self.modified_var.set(False)
        self.disk_entry.delete(0, tk.END)
    
    def _save(self):
        entries = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            entries.append(PageTableEntry(
                page_number=int(values[0]),
                present=values[1] == "1",
                frame_number=int(values[2]) if values[2] != "-" else -1,
                modified=values[3] == "1",
                disk_location=values[4]
            ))
        
        self.on_save(entries)
        self.window.destroy() 