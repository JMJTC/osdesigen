import tkinter as tk
from tkinter import ttk
from collections import deque


class PageTableEntry:

    def __init__(self, disk_location):
        self.frame = None  # 内存块号
        self.present = False  # 存在标志
        self.modified = False  # 修改标志
        self.disk_location = disk_location  # 磁盘位置


class Job:
    def __init__(self, num_pages, allocated_frames):
        self.page_table = [PageTableEntry(f"disk_{i}") for i in range(num_pages)]
        self.allocated_frames = allocated_frames  # 分配的内存块数
        self.frame_queue = deque()  # 用于FIFO置换
        self.used_frames = set()  # 已使用的内存块


class MemoryManager:
    def __init__(self):
        self.total_memory = 64 * 1024  # 64KB
        self.block_size = 1024  # 1KB/块
        self.num_blocks = self.total_memory // self.block_size
        self.jobs = []

    def create_job(self, num_pages, allocated_frames):
        if allocated_frames > self.num_blocks:
            return False
        self.jobs.append(Job(num_pages, allocated_frames))
        return True

    def access_memory(self, job_index, logical_address):
        job = self.jobs[job_index]
        page_number = (logical_address >> 10) & 0x3F  # 提取页号（6位）
        offset = logical_address & 0x3FF  # 页内偏移（10位）

        if page_number >= len(job.page_table):
            return None, "页号越界"

        entry = job.page_table[page_number]
        if entry.present:
            physical_address = (entry.frame << 10) | offset
            return physical_address, None

        # 处理缺页中断
        return self.handle_page_fault(job, page_number, offset)

    def handle_page_fault(self, job, page_number, offset):
        entry = job.page_table[page_number]

        # 尝试找到空闲块
        if len(job.used_frames) < job.allocated_frames:
            # 分配新块
            frame = len(job.used_frames)
            job.used_frames.add(frame)
            job.frame_queue.append(page_number)
        else:
            # 使用FIFO置换
            victim_page = job.frame_queue.popleft()
            victim_entry = job.page_table[victim_page]

            # 写回被修改的页
            if victim_entry.modified:
                self.write_to_disk(victim_entry)

            victim_entry.present = False
            frame = victim_entry.frame
            job.frame_queue.append(page_number)

        # 调入新页
        self.load_from_disk(entry, frame)
        entry.present = True
        entry.frame = frame
        entry.modified = False

        physical_address = (frame << 10) | offset
        return physical_address, page_number

    def load_from_disk(self, entry, frame):
        # 模拟从磁盘加载
        pass

    def write_to_disk(self, entry):
        # 模拟写回磁盘
        entry.modified = False


class PageSimulator:
    def __init__(self, root):
        self.root = root
        self.mm = MemoryManager()
        self.current_job = 0
        
        # 设置主题颜色
        self.colors = {
            'bg': '#f0f0f0',
            'primary': '#2196F3',
            'secondary': '#757575',
            'success': '#4CAF50',
            'error': '#f44336',
            'text': '#212121',
            'light_bg': '#ffffff'
        }
        
        # 配置根窗口
        self.root.configure(bg=self.colors['bg'])
        self.root.option_add('*Font', ('Microsoft YaHei UI', 10))
        
        self.create_widgets()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 左侧配置面板
        config_frame = ttk.LabelFrame(main_frame, text="配置面板", padding=15)
        config_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 创建作业配置
        job_frame = ttk.LabelFrame(config_frame, text="创建新作业", padding=10)
        job_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(job_frame, text="页数:").pack(anchor=tk.W)
        self.pages_entry = ttk.Entry(job_frame, width=20)
        self.pages_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(job_frame, text="分配块数:").pack(anchor=tk.W)
        self.frames_entry = ttk.Entry(job_frame, width=20)
        self.frames_entry.pack(fill=tk.X, pady=(0, 5))
        
        create_btn = ttk.Button(job_frame, text="创建作业", command=self.create_job, style='Accent.TButton')
        create_btn.pack(fill=tk.X, pady=5)
        
        # 内存访问
        access_frame = ttk.LabelFrame(config_frame, text="内存访问", padding=10)
        access_frame.pack(fill=tk.X)
        
        ttk.Label(access_frame, text="逻辑地址:").pack(anchor=tk.W)
        self.addr_entry = ttk.Entry(access_frame, width=20)
        self.addr_entry.pack(fill=tk.X, pady=(0, 5))
        
        access_btn = ttk.Button(access_frame, text="访问", command=self.access_memory, style='Accent.TButton')
        access_btn.pack(fill=tk.X, pady=5)
        
        # 右侧显示面板
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 页表显示
        table_frame = ttk.LabelFrame(display_frame, text="页表", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建表格样式
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=('Microsoft YaHei UI', 10, 'bold'))
        
        self.page_table = ttk.Treeview(table_frame, columns=('page', 'frame', 'present', 'modified'), 
                                      show='headings', style="Treeview")
        self.page_table.heading('page', text='页号')
        self.page_table.heading('frame', text='块号')
        self.page_table.heading('present', text='在内存')
        self.page_table.heading('modified', text='已修改')
        
        # 设置列宽
        self.page_table.column('page', width=100)
        self.page_table.column('frame', width=100)
        self.page_table.column('present', width=100)
        self.page_table.column('modified', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.page_table.yview)
        self.page_table.configure(yscrollcommand=scrollbar.set)
        
        self.page_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 日志显示
        log_frame = ttk.LabelFrame(display_frame, text="运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=('Microsoft YaHei UI', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 创建自定义按钮样式
        style.configure('Accent.TButton', 
                       background=self.colors['primary'],
                       foreground='white',
                       padding=5)
        
    def create_job(self):
        try:
            pages = int(self.pages_entry.get())
            frames = int(self.frames_entry.get())
            if pages < 1 or frames < 1:
                raise ValueError
            if self.mm.create_job(pages, frames):
                self.log(f"创建作业成功：{pages}页，分配{frames}块")
            else:
                self.log("创建失败：超出内存限制")
        except:
            self.log("输入无效")

    def access_memory(self):
        try:
            addr = int(self.addr_entry.get())
            physical, page_fault = self.mm.access_memory(self.current_job, addr)
            job = self.mm.jobs[self.current_job]

            if page_fault is not None:
                self.log(f"缺页中断！调入页 {page_fault}")

            self.log(f"逻辑地址: {addr} ({bin(addr)})")
            self.log(f"物理地址: {physical} ({bin(physical) if physical else '无效'})")

            # 更新页表显示
            self.update_page_table(job)
        except Exception as e:
            self.log(f"错误: {str(e)}")

    def update_page_table(self, job):
        for row in self.page_table.get_children():
            self.page_table.delete(row)

        for i, entry in enumerate(job.page_table):
            values = (
                i,
                entry.frame if entry.present else "N/A",
                "是" if entry.present else "否",
                "是" if entry.modified else "否"
            )
            self.page_table.insert("", "end", values=values)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        # 根据消息类型设置不同的颜色
        if "错误" in message or "失败" in message:
            self.log_text.tag_add("error", "end-2c linestart", "end-1c")
            self.log_text.tag_config("error", foreground=self.colors['error'])
        elif "成功" in message:
            self.log_text.tag_add("success", "end-2c linestart", "end-1c")
            self.log_text.tag_config("success", foreground=self.colors['success'])


if __name__ == "__main__":
    root = tk.Tk()
    root.title("请求式分页管理模拟器")
    root.geometry("1000x700")  # 调整窗口大小
    app = PageSimulator(root)
    root.mainloop()