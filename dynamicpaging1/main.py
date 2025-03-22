import tkinter as tk
from tkinter import ttk, messagebox
from models.page_table import PageTable, PageTableEntry
from models.page_replacement import FIFOStrategy
from gui.page_table_display import PageTableDisplay
from gui.instruction_panel import InstructionPanel
from gui.page_table_setup import PageTableSetup

class DynamicPagingSimulator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("动态分页管理模拟系统")
        self.window.geometry("1200x800")
        
        # 初始化页表（使用默认值）
        self.page_table = PageTable([
            PageTableEntry(0, True, 5, False, "010"),
            PageTableEntry(1, True, 8, False, "012"),
            PageTableEntry(2, True, 9, False, "013"),
            PageTableEntry(3, True, 1, False, "021"),
            PageTableEntry(4, False, -1, False, "022"),
            PageTableEntry(5, False, -1, False, "023"),
            PageTableEntry(6, False, -1, False, "125")
        ])
        
        # 初始化页面置换策略
        self.replacement_strategy = FIFOStrategy(self.page_table)
        
        self.setup_gui()
    
    def setup_gui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建页表设置按钮
        ttk.Button(main_frame, text="设置页表", 
                  command=self.show_page_table_setup).grid(row=0, column=0, sticky=tk.W)
        
        # 创建页表显示区域
        self.page_table_display = PageTableDisplay(main_frame, self.page_table.entries)
        
        # 创建指令执行面板
        self.instruction_panel = InstructionPanel(main_frame, self.execute_instruction)
        
        # 创建结果显示区域
        self.result_frame = ttk.LabelFrame(main_frame, text="执行结果", padding="5")
        self.result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.result_text = tk.Text(self.result_frame, height=10, width=80)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def show_page_table_setup(self):
        setup_window = PageTableSetup(self.window, self.update_page_table)
        self.window.wait_window(setup_window.window)
    
    def update_page_table(self, entries):
        self.page_table = PageTable(entries)
        self.page_table_display.page_table = entries
        self.page_table_display.update_display()
    
    def execute_instruction(self, page_number: int, offset: int, operation: str):
        if page_number < 0 or offset < 0:
            self.result_text.insert(tk.END, "错误：请输入有效的数字\n")
            return
        
        try:
            if not (0 <= page_number < len(self.page_table.entries)):
                self.result_text.insert(tk.END, f"错误：页号 {page_number} 超出范围\n")
                return
                
            if not (0 <= offset < self.page_table.block_size):
                self.result_text.insert(tk.END, f"错误：页内地址 {offset} 超出范围\n")
                return
            
            # 检查页面是否在内存中
            page_entry = self.page_table.get_entry(page_number)
            if not page_entry.present:
                # 处理缺页中断
                new_frame = self.replacement_strategy.handle_page_fault(page_number)
                self.result_text.insert(tk.END, 
                    f"缺页中断处理：将页面 {page_number} 调入内存块 {new_frame}\n")
            
            # 计算物理地址
            physical_address = self.page_table.get_physical_address(page_number, offset)
            
            # 更新修改标志
            if operation in ["save", "-", "×", "÷"]:
                page_entry.modified = True
            
            # 显示结果
            self.result_text.insert(tk.END, 
                f"执行指令: {operation} {page_number} {offset}\n")
            self.result_text.insert(tk.END, 
                f"物理地址: {physical_address}\n")
            self.result_text.insert(tk.END, 
                f"缺页情况: {'不缺页' if page_entry.present else '缺页'}\n")
            self.result_text.insert(tk.END, "-" * 50 + "\n")
            
            # 更新显示
            self.page_table_display.update_display()
            
        except ValueError as e:
            self.result_text.insert(tk.END, f"错误：{str(e)}\n")
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    simulator = DynamicPagingSimulator()
    simulator.run() 