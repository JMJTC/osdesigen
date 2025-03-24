import tkinter as tk
from tkinter import ttk
import time

# --------------------------
# 模拟参数设置
# --------------------------
MEMORY_SIZE = 64 * 1024  # 64KB
BLOCK_SIZE = 1024        # 每块1024字节
JOB_ALLOC_FRAMES = 4     # 作业可用的内存块数量(简化为固定4块，可在界面中改成用户输入)
PAGE_TABLE_SIZE = 8       # 总共有多少页（可根据需求改成用户可输入/动态判断）
OFFSET_MAX = BLOCK_SIZE   # 页内地址最大值
ANIMATION_DURATION = 800  # 动画持续时间(毫秒)

# --------------------------
# 数据结构和模拟逻辑
# --------------------------
class PageTableEntry:
    """页表项：valid、frame、modified、disk_pos(可选)"""
    def __init__(self, valid=False, frame=None, modified=False):
        self.valid = valid
        self.frame = frame
        self.modified = modified

class PagingSimulation:
    """
    用于管理页表、内存块、以及执行指令时的页面调度逻辑。
    使用FIFO在已分配给作业的块中进行替换。
    """
    def __init__(self, num_pages=PAGE_TABLE_SIZE, allocated_frames=JOB_ALLOC_FRAMES):
        self.num_pages = num_pages
        self.allocated_frames = allocated_frames
        # 初始化页表(全部 invalid)
        self.page_table = [PageTableEntry() for _ in range(num_pages)]
        # FIFO 队列，存放当前在内存的页号(先进先出)
        self.fifo_queue = []
        # 为演示方便，假设作业最初加载前2页(可自行调整/可做成界面可配置)
        initial_loaded = min(allocated_frames, num_pages)
        for page_no in range(initial_loaded):
            self.page_table[page_no].valid = True
            self.page_table[page_no].frame = page_no  # 简单起见，令 frame号=页号
            self.fifo_queue.append(page_no)
        # 已用帧号集合(本例简化假设 frame号 与 page_no 一致，真实场景需记录实际物理块号)
        self.used_frames = set(self.fifo_queue)
        # 记录日志
        self.log_lines = []

    def execute(self, op, page_no, offset):
        """
        执行一次访问：操作op(字符串)、页号page_no(int)、页内地址offset(int)。
        返回 (log_info, replaced_page, loaded_page) 以便做动画或提示。
        - log_info: 字符串日志
        - replaced_page: 若发生替换，返回被淘汰的页号；否则 None
        - loaded_page: 若发生装载，返回装载的页号；否则 None
        """
        if page_no < 0 or page_no >= self.num_pages:
            msg = f"访问页号 {page_no} 超出范围(0~{self.num_pages - 1})"
            self.log(msg)
            return msg, None, None

        entry = self.page_table[page_no]
        replaced_page = None
        loaded_page = None

        if entry.valid:
            # 命中
            frame = entry.frame
            phys_addr = frame * BLOCK_SIZE + offset
            msg = f"访问页 {page_no} -> 命中, 物理地址={phys_addr}, 无缺页"
            if op == "save":
                entry.modified = True
        else:
            # 缺页
            msg = f"访问页 {page_no} -> 缺页中断, "
            if len(self.fifo_queue) < self.allocated_frames:
                # 还有空闲帧(或可用位置)
                # 简化：直接令 frame = page_no(若不重复)
                # 如果 page_no 已经在 used_frames 中就找一个空闲数字(真实场景下不会这么做)
                frame = self.find_free_frame()
                msg += f"使用空闲帧 {frame} "
            else:
                # FIFO 替换
                replaced_page = self.fifo_queue.pop(0)
                replaced_entry = self.page_table[replaced_page]
                freed_frame = replaced_entry.frame
                replaced_entry.valid = False
                replaced_entry.frame = None
                replaced_entry.modified = False  # 这里不一定要清，但为了演示
                self.used_frames.remove(freed_frame)

                msg += f"淘汰页 {replaced_page}, 释放帧 {freed_frame}, "

                # 分配给page_no
                frame = freed_frame

            entry.valid = True
            entry.frame = frame
            entry.modified = (op == "save")
            loaded_page = page_no
            self.fifo_queue.append(page_no)
            self.used_frames.add(frame)

            phys_addr = frame * BLOCK_SIZE + offset
            msg += f"装入页 {page_no}, 物理地址={phys_addr}"

        self.log(msg)
        return msg, replaced_page, loaded_page

    def find_free_frame(self):
        """
        简化：在 [0, ..., 63] 范围里找一个不在 used_frames 里的最小编号返回。
        """
        # 真实系统可能会从分配给作业的块列表里找，这里演示用。
        for f in range(64):  # 假设最大64块
            if f not in self.used_frames:
                return f
        return 0  # 理论上不会走到这里

    def log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {text}"
        self.log_lines.append(line)

    def get_page_table_snapshot(self):
        """返回当前页表信息，用于GUI显示"""
        data = []
        for i, e in enumerate(self.page_table):
            valid = 1 if e.valid else 0
            frame = e.frame if e.frame is not None else "-"
            modified = 1 if e.modified else 0
            data.append((i, valid, frame, modified))
        return data

    def reset(self):
        """重置模拟状态（示例：可自行定义重置策略）"""
        self.__init__(self.num_pages, self.allocated_frames)
        self.log("模拟状态已重置。")


# --------------------------
# 图形界面 + 动画
# --------------------------
class PagingAnimationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("请求式分页管理模拟(交互+动画示例)")
        # 创建模拟器
        self.sim = PagingSimulation()

        # 上方：操作输入区
        input_frame = tk.Frame(self.root)
        input_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        tk.Label(input_frame, text="页号：").pack(side=tk.LEFT)
        self.entry_page_no = tk.Entry(input_frame, width=5)
        self.entry_page_no.pack(side=tk.LEFT, padx=2)

        tk.Label(input_frame, text="页内地址：").pack(side=tk.LEFT)
        self.entry_offset = tk.Entry(input_frame, width=6)
        self.entry_offset.pack(side=tk.LEFT, padx=2)

        # 操作类型：+ - × / load save
        self.op_var = tk.StringVar(value="+")
        ops = ["+", "-", "×", "/", "load", "save"]
        for op in ops:
            r = tk.Radiobutton(input_frame, text=op, variable=self.op_var, value=op)
            r.pack(side=tk.LEFT, padx=2)

        # 执行按钮
        self.btn_exec = tk.Button(input_frame, text="执行", command=self.on_execute)
        self.btn_exec.pack(side=tk.LEFT, padx=10)

        # 中间：动画/可视化区域
        self.canvas = tk.Canvas(self.root, width=600, height=250, bg="white")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # 在画布上绘制“内存帧”与“页表”示意
        self.frame_rects = []  # 用来存储每个帧块对应的矩形、文本等信息
        self.page_rects = []   # 这里可以画一排页，展示其valid/frame等
        self.draw_static_scene()  # 初始绘制

        # 下方：日志显示 + 重置按钮
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.log_text = tk.Text(bottom_frame, width=80, height=8, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, padx=5)
        self.scrollbar = tk.Scrollbar(bottom_frame, command=self.log_text.yview)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.scrollbar.set)

        self.btn_reset = tk.Button(bottom_frame, text="重置", command=self.on_reset)
        self.btn_reset.pack(side=tk.LEFT, padx=10)

        self.update_log_display()

    def draw_static_scene(self):
        """
        绘制固定背景：若干帧块的矩形(示例中画4个方框表示分配的4块)，
        以及页表区(8页)。后面动态填充或更新显示。
        """
        self.canvas.delete("all")
        # 绘制内存帧(演示：只画4块)
        x0, y0 = 50, 50
        w, h = 80, 50
        gap = 20
        for i in range(self.sim.allocated_frames):
            rect_id = self.canvas.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#f0f0f0")
            text_id = self.canvas.create_text(x0 + w/2, y0 + h/2, text=f"Frame {i}", font=("Arial", 10))
            self.frame_rects.append((rect_id, text_id))
            x0 += (w + gap)

        # 绘制页表区(简化：一排8页)
        x0, y0 = 50, 150
        w, h = 40, 30
        gap = 10
        for page_no in range(self.sim.num_pages):
            rect_id = self.canvas.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#e0ffff")
            text_id = self.canvas.create_text(x0 + w/2, y0 + h/2, text=f"P{page_no}", font=("Arial", 10))
            self.page_rects.append((rect_id, text_id))
            x0 += (w + gap)

        self.update_canvas_state()

    def update_canvas_state(self):
        """
        根据 self.sim 中的页表状态，更新 Canvas 中每个“Frame”方框和“Page”方框的显示
        """
        # 先把所有 Frame 标成空
        for i, (rect_id, text_id) in enumerate(self.frame_rects):
            self.canvas.itemconfig(rect_id, fill="#f0f0f0")
            self.canvas.itemconfig(text_id, text=f"Frame {i}")

        # 根据页表，找出哪些页面有效，以及它们对应的帧
        for page_no, entry in enumerate(self.sim.page_table):
            rect_id, text_id = self.page_rects[page_no]
            if entry.valid:
                # 标记此页为 valid
                self.canvas.itemconfig(rect_id, fill="#b3ecff")
                # 在对应的帧中显示它
                if entry.frame is not None and entry.frame < len(self.frame_rects):
                    f_rect, f_text = self.frame_rects[entry.frame]
                    self.canvas.itemconfig(f_rect, fill="#caffca")  # 有页面占用
                    self.canvas.itemconfig(f_text, text=f"F{entry.frame}\n<-P{page_no}")
            else:
                # 标记此页为 invalid
                self.canvas.itemconfig(rect_id, fill="#e0ffff")

    def on_execute(self):
        """执行一次访问"""
        page_str = self.entry_page_no.get().strip()
        offset_str = self.entry_offset.get().strip()
        op = self.op_var.get()

        if not page_str.isdigit() or not offset_str.isdigit():
            self.log("页号/偏移量必须是整数！")
            return
        page_no = int(page_str)
        offset = int(offset_str)
        if offset < 0 or offset >= BLOCK_SIZE:
            self.log(f"页内地址应在 [0, {BLOCK_SIZE-1}] 范围内")
            return

        msg, replaced_page, loaded_page = self.sim.execute(op, page_no, offset)
        self.log(msg)
        self.update_log_display()

        # 执行后做动画：如果发生替换/加载，就高亮
        self.animate_replacement(replaced_page, loaded_page)

    def animate_replacement(self, replaced_page, loaded_page):
        """
        简单动画：高亮被淘汰的页(若有)，以及新加载的页(若有)。
        """
        # 被淘汰的页 -> 红色闪烁
        if replaced_page is not None:
            rect_id, text_id = self.page_rects[replaced_page]
            self.flash_color(rect_id, from_color="#e0ffff", to_color="red", duration=ANIMATION_DURATION)

        # 新加载的页 -> 绿色闪烁
        if loaded_page is not None:
            rect_id, text_id = self.page_rects[loaded_page]
            self.flash_color(rect_id, from_color="#e0ffff", to_color="green", duration=ANIMATION_DURATION)

        # 等待动画结束后再更新整体状态
        self.root.after(ANIMATION_DURATION, self.update_canvas_state)

    def flash_color(self, rect_id, from_color, to_color, duration=500):
        """
        将指定矩形从 from_color 闪烁到 to_color，再闪回，持续 duration 毫秒。
        这里只做简单的 2 次切换。
        """
        half = duration // 2
        self.canvas.itemconfig(rect_id, fill=to_color)
        # half 毫秒后变回
        self.root.after(half, lambda: self.canvas.itemconfig(rect_id, fill=from_color))

    def on_reset(self):
        self.sim.reset()
        self.log("重置模拟器")
        self.update_canvas_state()
        self.update_log_display()

    def log(self, text):
        """在模拟器和文本框中记录日志"""
        self.sim.log(text)

    def update_log_display(self):
        """刷新日志文本区"""
        self.log_text.delete("1.0", tk.END)
        for line in self.sim.log_lines:
            self.log_text.insert(tk.END, line + "\n")
        self.log_text.see(tk.END)


# --------------------------
# 启动
# --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    gui = PagingAnimationGUI(root)
    root.mainloop()
