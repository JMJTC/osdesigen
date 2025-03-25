import tkinter as tk
from tkinter import messagebox
from simulation.paging_simulation import PagingSimulation
from gui.paging_animation_gui import PagingAnimationGUI

MEMORY_SIZE = 64 * 1024  # 64KB
BLOCK_SIZE = 1024  # 每块 1KB
MAX_BLOCKS = MEMORY_SIZE // BLOCK_SIZE  # 64
MAX_PAGES = 64  # 作业最多可有 64 页(页号范围 0~63)
OFFSET_MAX = BLOCK_SIZE  # 页内地址最大值(0~1023)
ANIMATION_DURATION = 800  # 动画持续时间(毫秒)


# --------------------------
# 配置窗口：用户输入
#  1. 作业页数(1~64)
#  2. 给作业分配的具体物理块号(逗号分隔)
# --------------------------
class ConfigWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("请求分页模拟 - 配置")
        self.create_widgets()
        self.sim_window = None

    def create_widgets(self):
        # 创建一个Frame容器
        frm = tk.Frame(self.root)
        # 将Frame容器放置在窗口中，并设置内边距
        frm.pack(padx=20, pady=20)

        # 创建一个标签，显示文本"作业页数(1~64):"
        tk.Label(frm, text="作业页数(1~64):").grid(row=0, column=0, pady=5, sticky=tk.E)
        # 创建一个Entry控件，用于输入作业页数
        self.entry_pages = tk.Entry(frm, width=10)
        # 将Entry控件放置在窗口中，并设置内边距
        self.entry_pages.grid(row=0, column=1, pady=5, sticky=tk.W)
        # 设置默认值为8页
        self.entry_pages.insert(0, "8")

        # 创建一个标签，显示文本"分配的物理块号(逗号分隔,如5,8,9,1):"
        tk.Label(frm, text="分配的物理块号(逗号分隔,如5,8,9,1):").grid(row=1, column=0, pady=5, sticky=tk.E)
        # 创建一个Entry控件，用于输入分配的物理块号
        self.entry_frames = tk.Entry(frm, width=20)
        # 将Entry控件放置在窗口中，并设置内边距
        self.entry_frames.grid(row=1, column=1, pady=5, sticky=tk.W)
        # 设置默认值为5,8,9,1
        self.entry_frames.insert(0, "5,8,9,1")

        # 创建一个按钮，点击后调用start_sim方法
        btn_start = tk.Button(frm, text="开始模拟", command=self.start_sim)
        # 将按钮放置在窗口中，并设置内边距
        btn_start.grid(row=2, column=0, columnspan=2, pady=15)

    def start_sim(self):
        # 获取用户输入的作业页数
        pages_str = self.entry_pages.get().strip()
        # 获取用户输入的物理块号列表
        frames_str = self.entry_frames.get().strip()
        # 检查作业页数是否为整数
        if not pages_str.isdigit():
            messagebox.showerror("输入错误", "作业页数必须是整数！")
            return

        # 将作业页数转换为整数
        num_pages = int(pages_str)
        # 检查作业页数是否在1~MAX_PAGES之间
        if not (1 <= num_pages <= MAX_PAGES):
            messagebox.showerror("输入错误", f"作业页数必须在1~{MAX_PAGES}之间！")
            return

        # 解析物理块号列表
        try:
            # 将物理块号列表中的每个元素转换为整数
            allocated_frames_list = [int(x.strip()) for x in frames_str.split(",") if x.strip() != ""]
        except:
            messagebox.showerror("输入错误", "分配的物理块号格式错误，请输入逗号分隔的整数。")
            return

        # 检查物理块号列表是否为空
        if not allocated_frames_list:
            messagebox.showerror("输入错误", "请至少输入一个物理块号。")
            return

        # 检查物理块号是否在0~MAX_BLOCKS-1之间
        for fno in allocated_frames_list:
            if fno < 0 or fno >= MAX_BLOCKS:
                messagebox.showerror("输入错误", f"块号 {fno} 超出 [0..{MAX_BLOCKS - 1}] 范围！")
                return

        # 去重（如果用户输入重复的块号，这里可做处理）
        # 如果需要强制不允许重复，可以做如下检查
        if len(set(allocated_frames_list)) < len(allocated_frames_list):
            messagebox.showwarning("警告", "输入的物理块号中有重复，系统将自动忽略重复项。")
            # 去重并排序
            allocated_frames_list = list(set(allocated_frames_list))
            allocated_frames_list.sort()

        # 启动模拟界面
        self.sim_window = tk.Toplevel(self.root)
        PagingAnimationGUI(self.sim_window, num_pages, allocated_frames_list)