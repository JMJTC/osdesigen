# main.py
import tkinter as tk
from tkinter import ttk, messagebox
from dynamic_partition import DynamicPartitionManager
from dynamic_paging import PagingManager


class MemoryManagementApp:
    def __init__(self, root):
        # 创建主窗口和笔记本式标签页
        self.root = root
        self.root.title("内存管理模拟器")
        self.notebook = ttk.Notebook(root)

        # 创建笔记本式窗口
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 动态分区管理标签页
        self.frame_partition = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_partition, text="动态分区管理")
        self.create_partition_ui()

        # 分页管理标签页
        self.frame_paging = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_paging, text="分页管理")
        self.create_paging_ui()

        # 初始化管理器
        self.partition_manager = DynamicPartitionManager()
        self.paging_manager = PagingManager()

    def create_partition_ui(self):
        # 分区管理界面组件
        frame = self.frame_partition

        # 控制面板
        ctrl_frame = ttk.LabelFrame(frame, text="操作控制")
        ctrl_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(ctrl_frame, text="内存大小:").grid(row=0, column=0)
        self.partition_size = ttk.Entry(ctrl_frame)
        self.partition_size.grid(row=0, column=1)
        ttk.Button(ctrl_frame, text="初始化内存",
                   command=self.init_partition).grid(row=0, column=2)

        ttk.Label(ctrl_frame, text="进程ID:").grid(row=1, column=0)
        self.pid_entry = ttk.Entry(ctrl_frame)
        self.pid_entry.grid(row=1, column=1)

        ttk.Label(ctrl_frame, text="操作类型:").grid(row=1, column=2)
        self.partition_op = ttk.Combobox(ctrl_frame, values=["分配", "回收"])
        self.partition_op.grid(row=1, column=3)

        ttk.Label(ctrl_frame, text="大小:").grid(row=1, column=4)
        self.size_entry = ttk.Entry(ctrl_frame)
        self.size_entry.grid(row=1, column=5)

        ttk.Label(ctrl_frame, text="算法:").grid(row=1, column=6)
        self.algorithm = ttk.Combobox(ctrl_frame,
                                      values=["最先适应", "最佳适应", "最坏适应"])
        self.algorithm.grid(row=1, column=7)

        ttk.Button(ctrl_frame, text="执行操作",
                   command=self.handle_partition_op).grid(row=1, column=8)

        # 显示面板
        display_frame = ttk.LabelFrame(frame, text="内存状态")
        display_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.partition_display = tk.Text(display_frame, height=15)
        self.partition_display.pack(fill=tk.BOTH, expand=True)

    def create_paging_ui(self):
        # 分页管理界面组件
        frame = self.frame_paging

        # 控制面板
        ctrl_frame = ttk.LabelFrame(frame, text="操作控制")
        ctrl_frame.pack(padx=10, pady=5, fill=tk.X)

        ttk.Label(ctrl_frame, text="作业ID:").grid(row=0, column=0)
        self.job_id = ttk.Entry(ctrl_frame)
        self.job_id.grid(row=0, column=1)

        ttk.Label(ctrl_frame, text="逻辑地址:").grid(row=0, column=2)
        self.logical_addr = ttk.Entry(ctrl_frame)
        self.logical_addr.grid(row=0, column=3)

        ttk.Button(ctrl_frame, text="执行访问",
                   command=self.handle_paging_op).grid(row=0, column=4)

        # 显示面板
        display_frame = ttk.LabelFrame(frame, text="访问结果")
        display_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.result_text = tk.Text(display_frame, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 页表显示
        self.page_table_display = ttk.LabelFrame(frame, text="页表状态")
        self.page_table_display.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    def init_partition(self):
        try:
            size = int(self.partition_size.get())
            self.partition_manager.initialize_memory(size)
            self.update_partition_display()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的内存大小")

    def handle_partition_op(self):
        pid = self.pid_entry.get()
        op = self.partition_op.get()
        algorithm = self.algorithm.get()

        try:
            if op == "分配":
                size = int(self.size_entry.get())
                success = self.partition_manager.allocate(pid, size, algorithm)
                if not success:
                    messagebox.showinfo("提示", "内存分配失败，没有足够的空间")
            else:
                self.partition_manager.deallocate(pid)

            self.update_partition_display()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")

    def update_partition_display(self):
        self.partition_display.delete(1.0, tk.END)
        partitions = self.partition_manager.get_memory_status()
        self.partition_display.insert(tk.END, "当前内存状态:\n")
        for p in partitions:
            status = "空闲" if p['free'] else f"进程 {p['pid']}"
            self.partition_display.insert(tk.END,
                                          f"起始地址: {p['start']:6d} | 大小: {p['size']:6d} | 状态: {status}\n")

    def handle_paging_op(self):
        job_id = self.job_id.get()
        try:
            addr = int(self.logical_addr.get())
            result = self.paging_manager.access_memory(job_id, addr)

            # 显示访问结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END,
                                    f"逻辑地址: {addr}\n物理地址: {result['physical_addr']}\n")
            if result['page_fault']:
                self.result_text.insert(tk.END,
                                        f"缺页中断发生，置换页面: {result['replaced_page']}\n")

            # 更新页表显示
            for widget in self.page_table_display.winfo_children():
                widget.destroy()

            pt = self.paging_manager.get_page_table(job_id)
            if pt:
                columns = ("页号", "块号", "在内存中", "修改过", "磁盘位置")
                tree = ttk.Treeview(self.page_table_display, columns=columns, show="headings")
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=80)

                for page, data in pt.items():
                    tree.insert("", tk.END, values=(
                        page,
                        data['frame'] if data['present'] else "N/A",
                        "✓" if data['present'] else "✗",
                        "✓" if data['dirty'] else "✗",
                        data['disk_location']
                    ))
                tree.pack(fill=tk.BOTH, expand=True)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的逻辑地址")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = MemoryManagementApp(root)
    root.mainloop()
