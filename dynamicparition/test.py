import tkinter as tk
from tkinter import ttk, messagebox

class MemoryManager:
    def __init__(self, total_memory):
        self.total_memory = total_memory
        self.free_blocks = [{'start': 0, 'size': total_memory}]
        self.allocated_blocks = {}
        self.next_process_id = 1
        self.history = []  # 操作历史
        self.current_history_index = -1

    def get_memory_usage(self):
        used_memory = sum(block['size'] for block in self.allocated_blocks.values())
        return (used_memory / self.total_memory) * 100

    def get_fragmentation(self):
        if not self.free_blocks:
            return 0
        total_free = sum(block['size'] for block in self.free_blocks)
        max_free = max(block['size'] for block in self.free_blocks)
        return ((max_free / total_free) - 1) * 100 if total_free > 0 else 0

    def save_state(self):
        self.current_history_index += 1
        self.history = self.history[:self.current_history_index]
        self.history.append({
            'free_blocks': self.free_blocks.copy(),
            'allocated_blocks': self.allocated_blocks.copy(),
            'next_process_id': self.next_process_id
        })

    def undo(self):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            state = self.history[self.current_history_index]
            self.free_blocks = state['free_blocks'].copy()
            self.allocated_blocks = state['allocated_blocks'].copy()
            self.next_process_id = state['next_process_id']
            return True
        return False

    def redo(self):
        if self.current_history_index < len(self.history) - 1:
            self.current_history_index += 1
            state = self.history[self.current_history_index]
            self.free_blocks = state['free_blocks'].copy()
            self.allocated_blocks = state['allocated_blocks'].copy()
            self.next_process_id = state['next_process_id']
            return True
        return False

    def allocate(self, size, algorithm):
        self.save_state()
        if algorithm == 'first_fit':
            return self._allocate_first_fit(size)
        elif algorithm == 'best_fit':
            return self._allocate_best_fit(size)
        elif algorithm == 'worst_fit':
            return self._allocate_worst_fit(size)
        return None

    def _allocate_first_fit(self, size):
        for i, block in enumerate(self.free_blocks):
            if block['size'] >= size:
                return self._split_block(i, block, size)
        return None

    def _allocate_best_fit(self, size):
        best_idx = -1
        min_size = float('inf')
        for i, block in enumerate(self.free_blocks):
            if size <= block['size'] < min_size:
                best_idx = i
                min_size = block['size']
        if best_idx == -1:
            return None
        return self._split_block(best_idx, self.free_blocks[best_idx], size)

    def _allocate_worst_fit(self, size):
        if not self.free_blocks:
            return None
        worst_idx = max(range(len(self.free_blocks)),
                      key=lambda i: self.free_blocks[i]['size'])
        block = self.free_blocks[worst_idx]
        if block['size'] < size:
            return None
        return self._split_block(worst_idx, block, size)

    def _split_block(self, index, block, size):
        new_start = block['start'] + size
        new_size = block['size'] - size
        del self.free_blocks[index]
        if new_size > 0:
            self.free_blocks.insert(index, {'start': new_start, 'size': new_size})
        pid = self.next_process_id
        self.allocated_blocks[pid] = {'start': block['start'], 'size': size}
        self.next_process_id += 1
        return pid

    def deallocate(self, pid):
        self.save_state()
        if pid not in self.allocated_blocks:
            return False
        block = self.allocated_blocks[pid]
        self.free_blocks.append({'start': block['start'], 'size': block['size']})
        del self.allocated_blocks[pid]
        self._merge_blocks()
        return True

    def _merge_blocks(self):
        self.free_blocks.sort(key=lambda x: x['start'])
        i = 0
        while i < len(self.free_blocks)-1:
            current = self.free_blocks[i]
            next_block = self.free_blocks[i+1]
            if current['start'] + current['size'] == next_block['start']:
                current['size'] += next_block['size']
                del self.free_blocks[i+1]
            else:
                i += 1

class MemorySimulator:
    def __init__(self, root):
        self.root = root
        self.memory = MemoryManager(1024)
        self.root.configure(bg='#f0f0f0')
        self.create_widgets()
        self.update_display()
        self.setup_shortcuts()

    def setup_shortcuts(self):
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
        
        self.canvas = tk.Canvas(canvas_frame, height=120, bg='white', highlightthickness=1, highlightbackground='#cccccc')
        self.canvas.pack(fill=tk.X)
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
        status_frame = tk.Frame(self.root, bg='#f0f0f0')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.usage_label = tk.Label(status_frame, text="内存使用率: 0%", bg='#f0f0f0', font=('微软雅黑', 9))
        self.usage_label.pack(side=tk.LEFT, padx=5)
        
        self.frag_label = tk.Label(status_frame, text="碎片率: 0%", bg='#f0f0f0', font=('微软雅黑', 9))
        self.frag_label.pack(side=tk.LEFT, padx=5)

    def show_hover_info(self, event):
        # 获取鼠标位置对应的内存块信息
        x = event.x
        total = self.memory.total_memory
        width = self.canvas.winfo_width()
        
        for pid, info in self.memory.allocated_blocks.items():
            x1 = (info['start'] / total) * width
            x2 = ((info['start'] + info['size']) / total) * width
            if x1 <= x <= x2:
                self.canvas.delete("hover")
                self.canvas.create_text(x, 20, text=f"进程 {pid}\n大小: {info['size']}KB",
                                     fill='blue', tags="hover", font=('微软雅黑', 8))
                return

        for block in self.memory.free_blocks:
            x1 = (block['start'] / total) * width
            x2 = ((block['start'] + block['size']) / total) * width
            if x1 <= x <= x2:
                self.canvas.delete("hover")
                self.canvas.create_text(x, 20, text=f"空闲块\n大小: {block['size']}KB",
                                     fill='red', tags="hover", font=('微软雅黑', 8))
                return

        self.canvas.delete("hover")

    def set_total_memory(self):
        try:
            new_size = int(self.total_memory_var.get())
            if new_size <= 0:
                raise ValueError
            self.memory = MemoryManager(new_size)
            self.update_display()
            self.info_text.insert(tk.END, f"内存大小已设置为 {new_size}KB\n")
        except:
            messagebox.showerror("错误", "请输入有效的正整数大小")

    def handle_undo(self):
        if self.memory.undo():
            self.update_display()
            self.info_text.insert(tk.END, "已撤销上一步操作\n")

    def handle_redo(self):
        if self.memory.redo():
            self.update_display()
            self.info_text.insert(tk.END, "已重做操作\n")

    def update_display(self):
        # 更新Canvas显示
        self.canvas.delete("all")
        total = self.memory.total_memory
        width = self.canvas.winfo_width()

        # 收集所有块
        blocks = []
        for pid, info in self.memory.allocated_blocks.items():
            blocks.append((info['start'], info['size'], 'allocated', pid))
        for block in self.memory.free_blocks:
            blocks.append((block['start'], block['size'], 'free', None))
        blocks.sort()

        # 绘制块
        for start, size, typ, pid in blocks:
            x1 = (start / total) * width
            x2 = ((start + size) / total) * width
            color = '#4CAF50' if typ == 'free' else '#2196F3'  # 使用更柔和的颜色
            self.canvas.create_rectangle(x1, 10, x2, 90, fill=color, outline='#ffffff')
            text = f"{start}-{start+size}\n{size}KB"
            self.canvas.create_text((x1+x2)/2, 50, text=text, fill='white', font=('微软雅黑', 8))

        # 更新表格
        for row in self.free_table.get_children():
            self.free_table.delete(row)
        for block in self.memory.free_blocks:
            self.free_table.insert("", 'end', values=(block['start'], block['size']))

        for row in self.alloc_table.get_children():
            self.alloc_table.delete(row)
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
            self.info_text.insert(tk.END, f"分配失败，内存不足 (请求: {size}KB, 最大可用: {max(block['size'] for block in self.memory.free_blocks)}KB)\n")
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

if __name__ == "__main__":
    root = tk.Tk()
    root.title("动态分区管理模拟器")
    root.geometry("800x600")  # 设置默认窗口大小
    app = MemorySimulator(root)
    root.mainloop()