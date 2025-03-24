import tkinter as tk
from tkinter import ttk
from typing import Callable

class InstructionPanel:
    def __init__(self, parent: ttk.Frame, on_execute: Callable[[int, int, str], None]):
        self.frame = ttk.LabelFrame(parent, text="指令执行", padding="5")
        self.frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.on_execute = on_execute
        
        # 指令输入
        ttk.Label(self.frame, text="页号:").grid(row=0, column=0, padx=5)
        self.page_entry = ttk.Entry(self.frame, width=10)
        self.page_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.frame, text="页内地址:").grid(row=0, column=2, padx=5)
        self.offset_entry = ttk.Entry(self.frame, width=10)
        self.offset_entry.grid(row=0, column=3, padx=5)
        
        # 操作类型选择
        self.operation_var = tk.StringVar(value="+")
        operations = ["+", "-", "×", "÷", "load", "save"]
        for i, op in enumerate(operations):
            ttk.Radiobutton(self.frame, text=op, variable=self.operation_var, 
                          value=op).grid(row=0, column=4+i, padx=5)
        
        # 执行按钮
        ttk.Button(self.frame, text="执行", 
                  command=self._execute).grid(row=0, column=10, padx=5)
    
    def _execute(self):
        try:
            page_number = int(self.page_entry.get())
            offset = int(self.offset_entry.get())
            operation = self.operation_var.get()
            self.on_execute(page_number, offset, operation)
        except ValueError:
            # 错误处理将在主程序中完成
            self.on_execute(-1, -1, "") 