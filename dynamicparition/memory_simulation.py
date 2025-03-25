import tkinter as tk
from tkinter import ttk, messagebox
from memory_manager import MemoryManager


class MemorySimulator:
    def __init__(self, root):
        # 初始化函数，设置根窗口，内存管理器，整体样式，创建小部件，更新显示，设置快捷键
        self.root = root
        self.memory = MemoryManager(1024)
        self.root.configure(bg='#f0f0f0')
        self.create_widgets()
        self.update_display()
        self.setup_shortcuts()

    def setup_shortcuts(self):
        # 绑定快捷键
        self.root.bind('<Control-z>', lambda e: self.handle_undo())
        self.root.bind('<Control-y>', lambda e: self.handle_redo())
        self.root.bind('<Return>', lambda e: self.handle_allocate())
        self.root.bind('<Delete>', lambda e: self.handle_deallocate())

    def create_widgets(self):
        # 设置整体样式
        style = ttk.Style()
        style.configure('Treeview', background='white', fieldbackground='white', foreground='black')
        style.configure('Treeview.Heading', background='#e1e1e1', foreground='black')
        style.configure('TLabelframe', background='#f0f0f0')
        style.configure('TLabelframe.Label', background='#f0f0f0', font=('微软雅黑', 10))
        style.configure('TButton', padding=5)
        style.configure('TEntry', padding=5)

        # 添加工具栏
        toolbar = tk.Frame(self.root, bg='#f0f0f0')
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Button(toolbar, text="撤销 (Ctrl+Z)", command=self.handle_undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="重做 (Ctrl+Y)", command=self.handle_redo).pack(side=tk.LEFT, padx=2)

        # 添加内存大小设置
        ttk.Label(toolbar, text="总内存大小:").pack(side=tk.LEFT, padx=5)
        self.total_memory_var = tk.StringVar(value="1024")
        self.total_memory_entry = ttk.Entry(toolbar, textvariable=self.total_memory_var, width=10)
        self.total_memory_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="设置", command=self.set_total_memory).pack(side=tk.LEFT, padx=2)

        # 左侧面板
        left_frame = tk.Frame(self.root, bg='#f0f0f0')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 内存可视化区域
        canvas_frame = tk.Frame(left_frame, bg='#f0f0f0')
        canvas_frame.pack(fill=tk.X, pady=(0, 10))

        self.canvas = tk.Canvas(canvas_frame, height=120, bg='white', highlightthickness=1,
                                highlightbackground='#cccccc')
        self.canvas.pack(fill=tk.X)
        # 绑定鼠标移动事件
        self.canvas.bind('<Motion>', self.show_hover_info)

        # 分区表
        table_frame = tk.Frame(left_frame, bg='#f0f0f0')
        table_frame.pack(fill=tk.BOTH, expand=True)

        # 空闲分区表
        free_label = tk.Label(table_frame, text="可用分区表", bg='#f0f0f0', font=('微软雅黑', 10, 'bold'))
        free_label.pack(pady=(0, 5))
        self.free_table = ttk.Treeview(table_frame, columns=('start', 'size'), show='headings', height=5)
        self.free_table.heading('start', text='起始地址')
        self.free_table.heading('size', text='大小')
        self.free_table.pack(fill=tk.X, pady=(0, 10))

        # 已分配分区表
        alloc_label = tk.Label(table_frame, text="已分配分区表", bg='#f0f0f0', font=('微软雅黑', 10, 'bold'))
        alloc_label.pack(pady=(0, 5))
        self.alloc_table = ttk.Treeview(table_frame, columns=('pid', 'start', 'size'), show='headings', height=5)
        self.alloc_table.heading('pid', text='进程ID')
        self.alloc_table.heading('start', text='起始地址')
        self.alloc_table.heading('size', text='大小')
        self.alloc_table.pack(fill=tk.X)

        # 右侧面板
        right_frame = tk.Frame(self.root, bg='#f0f0f0')
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # 算法选择
        algo_frame = ttk.LabelFrame(right_frame, text="分配算法", padding=10)
        algo_frame.pack(pady=(0, 10))
        self.algo_var = tk.StringVar(value='first_fit')
        algorithms = [('最先适应', 'first_fit'),
                      ('最佳适应', 'best_fit'),
                      ('最坏适应', 'worst_fit')]
        for text, value in algorithms:
            rb = ttk.Radiobutton(algo_frame, text=text, variable=self.algo_var,
                                 value=value)
            rb.pack(anchor=tk.W, pady=2)

        # 分配操作
        alloc_frame = ttk.LabelFrame(right_frame, text="分配内存", padding=10)
        alloc_frame.pack(pady=(0, 10))
        ttk.Label(alloc_frame, text="大小:").pack(anchor=tk.W)
        self.size_entry = ttk.Entry(alloc_frame)
        self.size_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(alloc_frame, text="分配", command=self.handle_allocate).pack(fill=tk.X)

        # 释放操作
        free_frame = ttk.LabelFrame(right_frame, text="释放内存", padding=10)
        free_frame.pack(pady=(0, 10))
        ttk.Label(free_frame, text="进程ID:").pack(anchor=tk.W)
        self.pid_entry = ttk.Entry(free_frame)
        self.pid_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(free_frame, text="释放", command=self.handle_deallocate).pack(fill=tk.X)

        # 信息显示
        info_frame = ttk.LabelFrame(right_frame, text="操作日志", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True)
        self.info_text = tk.Text(info_frame, height=10, width=30, bg='white',
                                 font=('Consolas', 9), padx=5, pady=5)
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # 添加状态栏
        # 创建一个Frame，用于显示内存使用率和碎片率
        # 创建一个Frame，用于显示状态信息
        status_frame = tk.Frame(left_frame, bg='#f0f0f0')
        # 将Frame放置在left_frame的底部，并填充水平空间，设置内边距
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # 创建一个Label，用于显示内存使用率
        # 创建一个标签，用于显示内存使用率
        self.usage_label = tk.Label(status_frame, text="内存使用率: 0%", bg='#f0f0f0', font=('微软雅黑', 9))
        # 将标签放置在status_frame中，并填充整个区域，左右各留出5个像素的间距
        self.usage_label.pack(fill=tk.BOTH, padx=5)

        # 创建一个Label，用于显示碎片率
        self.frag_label = tk.Label(status_frame, text="碎片率: 0%", bg='#f0f0f0', font=('微软雅黑', 9))
        self.frag_label.pack(fill=tk.BOTH, padx=5)


    def show_hover_info(self, event):
        # 获取鼠标位置对应的内存块信息
        # 获取鼠标点击位置的x坐标
        x = event.x
        # 获取内存总大小
        total = self.memory.total_memory
        # 获取画布的宽度
        width = self.canvas.winfo_width()

        # 遍历已分配的内存块
        for pid, info in self.memory.allocated_blocks.items():
            # 计算内存块在画布上的起始位置
            x1 = (info['start'] / total) * width
            # 计算内存块在画布上的结束位置
            x2 = ((info['start'] + info['size']) / total) * width
            # 如果鼠标位置在内存块内
            if x1 <= x <= x2:
                # 删除之前的提示信息
                self.canvas.delete("hover")
                # 在鼠标位置显示提示信息
                self.canvas.create_text(x, 20, text=f"进程 {pid}\n大小: {info['size']}KB",
                                        fill='blue', tags="hover", font=('微软雅黑', 8))
                # 返回，不再继续遍历
                return

        # 遍历内存中的空闲块
        for block in self.memory.free_blocks:
            # 计算空闲块在画布上的起始位置
            x1 = (block['start'] / total) * width
            # 计算空闲块在画布上的结束位置
            x2 = ((block['start'] + block['size']) / total) * width
            # 如果鼠标位置在空闲块范围内
            if x1 <= x <= x2:
                # 删除之前的提示信息
                self.canvas.delete("hover")
                # 在鼠标位置显示空闲块的大小
                self.canvas.create_text(x, 20, text=f"空闲块\n大小: {block['size']}KB",
                                        fill='red', tags="hover", font=('微软雅黑', 8))
                # 返回，不再继续遍历
                return

        # 如果鼠标位置不在任何空闲块范围内，删除之前的提示信息
        self.canvas.delete("hover")

    def set_total_memory(self):
        try:
            # 获取用户输入的内存大小
            new_size = int(self.total_memory_var.get())
            # 如果用户输入的内存大小小于等于0，则抛出异常
            if new_size <= 0:
                raise ValueError
            # 创建新的内存管理器
            self.memory = MemoryManager(new_size)
            # 更新显示
            self.update_display()
            # 在信息框中插入设置后的内存大小
            self.info_text.insert(tk.END, f"内存大小已设置为 {new_size}KB\n")
        except:
            # 如果用户输入的内存大小无效，则弹出错误提示框
            messagebox.showerror("错误", "请输入有效的正整数大小")

    def handle_undo(self):
        # 撤销上一步操作
        if self.memory.undo():
            self.update_display()
            self.info_text.insert(tk.END, "已撤销上一步操作\n")

    def handle_redo(self):
        # 重做操作
        if self.memory.redo():
            self.update_display()
            self.info_text.insert(tk.END, "已重做操作\n")

    def update_display(self):
        # 更新Canvas显示
        self.canvas.delete("all")
        # 获取总内存
        total = self.memory.total_memory
        # 获取Canvas宽度
        width = self.canvas.winfo_width()

        # 收集所有块
        # 创建一个空列表，用于存储内存块信息
        blocks = []
        # 遍历已分配的内存块
        for pid, info in self.memory.allocated_blocks.items():
            # 将已分配的内存块信息添加到列表中
            blocks.append((info['start'], info['size'], 'allocated', pid))
        # 遍历空闲的内存块
        for block in self.memory.free_blocks:
            # 将空闲的内存块信息添加到列表中
            blocks.append((block['start'], block['size'], 'free', None))
        # 对内存块信息进行排序
        blocks.sort()

        # 绘制块
        # 遍历每个块
        for start, size, typ, pid in blocks:
            # 计算块在画布上的位置
            x1 = (start / total) * width
            x2 = ((start + size) / total) * width
            # 根据块类型设置颜色
            color = '#4CAF50' if typ == 'free' else '#2196F3'  # 使用更柔和的颜色
            # 在画布上绘制矩形
            self.canvas.create_rectangle(x1, 10, x2, 90, fill=color, outline='#ffffff')
            # 在矩形上绘制文本
            text = f"{start}-{start + size}\n{size}KB"
            self.canvas.create_text((x1 + x2) / 2, 50, text=text, fill='white', font=('微软雅黑', 8))

        # 更新表格
        # 清空free_table中的所有行
        for row in self.free_table.get_children():
            self.free_table.delete(row)
        # 将free_blocks中的每个block插入到free_table中
        for block in self.memory.free_blocks:
            self.free_table.insert("", 'end', values=(block['start'], block['size']))

        # 清空alloc_table中的所有行
        for row in self.alloc_table.get_children():
            self.alloc_table.delete(row)
        # 将allocated_blocks中的每个block插入到alloc_table中
        for pid, info in self.memory.allocated_blocks.items():
            self.alloc_table.insert("", 'end', values=(pid, info['start'], info['size']))

        # 更新状态栏
        usage = self.memory.get_memory_usage()
        frag = self.memory.get_fragmentation()
        self.usage_label.config(text=f"内存使用率: {usage:.1f}%")
        self.frag_label.config(text=f"碎片率: {frag:.1f}%")

    def handle_allocate(self):
        try:
            size = int(self.size_entry.get())
            if size <= 0:
                raise ValueError
            if size > self.memory.total_memory:
                messagebox.showerror("错误", f"分配大小不能超过总内存大小({self.memory.total_memory}KB)")
                return
        except:
            messagebox.showerror("错误", "请输入有效的正整数大小")
            return

        pid = self.memory.allocate(size, self.algo_var.get())
        if pid:
            self.info_text.insert(tk.END, f"进程 {pid} 分配成功 (大小: {size}KB)\n")
        else:
            self.info_text.insert(tk.END,
                                  f"分配失败，内存不足 (请求: {size}KB, 最大可用: {max(block['size'] for block in self.memory.free_blocks)}KB)\n")
        self.update_display()

    def handle_deallocate(self):
        try:
            pid = int(self.pid_entry.get())
        except:
            messagebox.showerror("错误", "请输入有效的进程ID")
            return

        if self.memory.deallocate(pid):
            self.info_text.insert(tk.END, f"进程 {pid} 已释放\n")
        else:
            self.info_text.insert(tk.END, "无效的进程ID\n")
        self.update_display()
