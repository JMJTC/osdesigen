import tkinter as tk
from tkinter import ttk, messagebox
import time

MEMORY_SIZE = 64 * 1024    # 64KB
BLOCK_SIZE = 1024          # 每块 1KB
MAX_BLOCKS = MEMORY_SIZE // BLOCK_SIZE  # 64
MAX_PAGES = 64             # 作业最多可有 64 页(页号范围 0~63)
OFFSET_MAX = BLOCK_SIZE    # 页内地址最大值(0~1023)
ANIMATION_DURATION = 800   # 动画持续时间(毫秒)


class PageTableEntry:
    """页表项：valid、frame、modified"""
    def __init__(self, valid=False, frame=None, modified=False):
        self.valid = valid
        self.frame = frame
        self.modified = modified


class PagingSimulation:
    """
    使用“局部置换”（FIFO）模拟请求分页。
    用户指定：num_pages(页数)、allocated_frames_list(给作业分配的具体物理块号)。
    """
    def __init__(self, num_pages, allocated_frames_list):
        """
        :param num_pages: 作业拥有的页数(1~64)
        :param allocated_frames_list: 给作业分配的具体物理块号(list[int])，如 [5,8,9,1]
        """
        self.num_pages = num_pages
        # 给作业分配的块号（局部置换时只能用这些块）
        self.allocated_frames_list = allocated_frames_list
        # 初始化页表(全部 invalid)
        self.page_table = [PageTableEntry() for _ in range(num_pages)]

        # FIFO 队列：记录已经装入内存的页号(先进先出)
        self.fifo_queue = []
        # 记录已经使用的帧号（仅在 allocated_frames_list 范围内）
        self.used_frames = set()

        # 日志
        self.log_lines = []
        self.log(f"初始化：作业共有 {num_pages} 页，分配块号 {allocated_frames_list}。")

    def execute(self, op, page_no, offset):
        """
        执行一次访问:
        :param op: 操作类型 (字符串，如 +, -, ×, /, load, save)
        :param page_no: 访问的页号
        :param offset: 页内地址
        :return: (log_info, replaced_page, loaded_page)
                 - log_info: 字符串日志
                 - replaced_page: 若发生替换则返回被淘汰的页号，否则 None
                 - loaded_page: 若发生装载则返回新装入的页号，否则 None
        """
        replaced_page = None
        loaded_page = None

        # 检查页号范围
        if page_no < 0 or page_no >= self.num_pages:
            msg = f"访问页 {page_no} 超出作业页范围(0~{self.num_pages-1})"
            self.log(msg)
            return msg, None, None

        # 检查 offset 范围
        if offset < 0 or offset >= BLOCK_SIZE:
            msg = f"页内地址 {offset} 超出范围(0~{BLOCK_SIZE-1})"
            self.log(msg)
            return msg, None, None

        entry = self.page_table[page_no]
        if entry.valid:
            # 命中
            frame = entry.frame
            phys_addr = frame * BLOCK_SIZE + offset
            msg = f"访问页 {page_no} -> 命中, 物理地址={phys_addr}, 无缺页"
            if op == "save":
                entry.modified = True
        else:
            # 缺页中断
            msg = f"访问页 {page_no} -> 缺页中断, "
            # 若 FIFO 队列尚未装满 allocated_frames_list 的容量，就找空闲块
            if len(self.fifo_queue) < len(self.allocated_frames_list):
                frame = self.find_free_frame()
                msg += f"使用空闲帧 {frame}, "
            else:
                # FIFO 替换
                replaced_page = self.fifo_queue.pop(0)
                replaced_entry = self.page_table[replaced_page]
                freed_frame = replaced_entry.frame
                replaced_entry.valid = False
                replaced_entry.frame = None
                replaced_entry.modified = False
                self.used_frames.remove(freed_frame)

                msg += f"淘汰页 {replaced_page}, 释放帧 {freed_frame}, "
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
        在 allocated_frames_list 中找一个尚未使用的帧号返回(选最小或第一个可用)。
        """
        for f in self.allocated_frames_list:
            if f not in self.used_frames:
                return f
        # 理论上不会走到这里，因为若还没满就应该有可用帧
        return self.allocated_frames_list[0]

    def log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {text}"
        self.log_lines.append(line)

    def get_page_table_snapshot(self):
        """返回当前页表信息，用于GUI显示。每项为 (页号, valid, frame, modified)。"""
        data = []
        for i, e in enumerate(self.page_table):
            valid = 1 if e.valid else 0
            frame = e.frame if e.frame is not None else "-"
            modified = 1 if e.modified else 0
            data.append((i, valid, frame, modified))
        return data

    def reset(self):
        """重置模拟状态：全部无效，FIFO 队列清空，used_frames 清空。"""
        self.page_table = [PageTableEntry() for _ in range(self.num_pages)]
        self.fifo_queue = []
        self.used_frames = set()
        self.log_lines = []
        self.log("模拟状态已重置。")


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
        frm = tk.Frame(self.root)
        frm.pack(padx=20, pady=20)

        tk.Label(frm, text="作业页数(1~64):").grid(row=0, column=0, pady=5, sticky=tk.E)
        self.entry_pages = tk.Entry(frm, width=10)
        self.entry_pages.grid(row=0, column=1, pady=5, sticky=tk.W)
        self.entry_pages.insert(0, "8")  # 默认8页

        tk.Label(frm, text="分配的物理块号(逗号分隔,如5,8,9,1):").grid(row=1, column=0, pady=5, sticky=tk.E)
        self.entry_frames = tk.Entry(frm, width=20)
        self.entry_frames.grid(row=1, column=1, pady=5, sticky=tk.W)
        self.entry_frames.insert(0, "5,8,9,1")

        btn_start = tk.Button(frm, text="开始模拟", command=self.start_sim)
        btn_start.grid(row=2, column=0, columnspan=2, pady=15)

    def start_sim(self):
        pages_str = self.entry_pages.get().strip()
        frames_str = self.entry_frames.get().strip()
        if not pages_str.isdigit():
            messagebox.showerror("输入错误", "作业页数必须是整数！")
            return

        num_pages = int(pages_str)
        if not (1 <= num_pages <= MAX_PAGES):
            messagebox.showerror("输入错误", f"作业页数必须在1~{MAX_PAGES}之间！")
            return

        # 解析物理块号列表
        try:
            allocated_frames_list = [int(x.strip()) for x in frames_str.split(",") if x.strip() != ""]
        except:
            messagebox.showerror("输入错误", "分配的物理块号格式错误，请输入逗号分隔的整数。")
            return

        if not allocated_frames_list:
            messagebox.showerror("输入错误", "请至少输入一个物理块号。")
            return

        # 检查块号范围
        for fno in allocated_frames_list:
            if fno < 0 or fno >= MAX_BLOCKS:
                messagebox.showerror("输入错误", f"块号 {fno} 超出 [0..{MAX_BLOCKS-1}] 范围！")
                return

        # 去重（如果用户输入重复的块号，这里可做处理）
        # 如果需要强制不允许重复，可以做如下检查
        if len(set(allocated_frames_list)) < len(allocated_frames_list):
            messagebox.showwarning("警告", "输入的物理块号中有重复，系统将自动忽略重复项。")
            allocated_frames_list = list(set(allocated_frames_list))
            allocated_frames_list.sort()

        # 启动模拟界面
        self.sim_window = tk.Toplevel(self.root)
        PagingAnimationGUI(self.sim_window, num_pages, allocated_frames_list)


# --------------------------
# 动画界面：用户输入(页号、页内地址、操作)后执行
# --------------------------
class PagingAnimationGUI:
    def __init__(self, root, num_pages, allocated_frames_list):
        self.root = root
        self.root.title("请求分页管理模拟 - 交互动画")
        self.sim = PagingSimulation(num_pages, allocated_frames_list)

        # 操作输入区
        input_frame = tk.Frame(self.root)
        input_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        tk.Label(input_frame, text="页号：").pack(side=tk.LEFT)
        self.entry_page_no = tk.Entry(input_frame, width=5)
        self.entry_page_no.pack(side=tk.LEFT, padx=2)

        tk.Label(input_frame, text="页内地址：").pack(side=tk.LEFT)
        self.entry_offset = tk.Entry(input_frame, width=6)
        self.entry_offset.pack(side=tk.LEFT, padx=2)

        self.op_var = tk.StringVar(value="+")
        ops = ["+", "-", "×", "/", "load", "save"]
        for op in ops:
            r = tk.Radiobutton(input_frame, text=op, variable=self.op_var, value=op)
            r.pack(side=tk.LEFT, padx=2)

        self.btn_exec = tk.Button(input_frame, text="执行", command=self.on_execute)
        self.btn_exec.pack(side=tk.LEFT, padx=10)

        # 画布
        self.canvas = tk.Canvas(self.root, width=700, height=300, bg="white")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 日志显示
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.log_text = tk.Text(bottom_frame, width=80, height=8, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, padx=5)
        scrollbar = tk.Scrollbar(bottom_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.btn_reset = tk.Button(bottom_frame, text="重置", command=self.on_reset)
        self.btn_reset.pack(side=tk.LEFT, padx=10)

        # 可视化数据
        self.frame_rects = []  # (rect_id, text_id, frame_no)
        self.page_rects = []   # (rect_id, text_id, page_no)

        # 绘制静态场景
        self.draw_static_scene()
        self.update_log_display()

    def draw_static_scene(self):
        """
        绘制 allocated_frames_list 对应的方框，以及 num_pages 个“页”。
        """
        self.canvas.delete("all")

        # 绘制分配给作业的物理块
        x0, y0 = 50, 50
        w, h = 80, 40
        gap = 20
        for frame_no in self.sim.allocated_frames_list:
            rect_id = self.canvas.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#f0f0f0")
            text_id = self.canvas.create_text(x0 + w/2, y0 + h/2, text=f"Frame {frame_no}", font=("Arial", 10))
            self.frame_rects.append((rect_id, text_id, frame_no))
            x0 += (w + gap)

        # 绘制作业的页
        x0, y0 = 50, 150
        w, h = 40, 30
        gap = 10
        for page_no in range(self.sim.num_pages):
            rect_id = self.canvas.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#e0ffff")
            text_id = self.canvas.create_text(x0 + w/2, y0 + h/2, text=f"P{page_no}", font=("Arial", 10))
            self.page_rects.append((rect_id, text_id, page_no))
            x0 += (w + gap)

        self.update_canvas_state()

    def update_canvas_state(self):
        """
        根据 self.sim 的页表状态，更新 Canvas 中各个方框的显示。
        """
        # 所有块先恢复“空”状态
        for (rect_id, text_id, frame_no) in self.frame_rects:
            self.canvas.itemconfig(rect_id, fill="#f0f0f0")
            self.canvas.itemconfig(text_id, text=f"Frame {frame_no}")

        # 所有页根据 valid 来变色
        for (rect_id, text_id, page_no) in self.page_rects:
            entry = self.sim.page_table[page_no]
            if entry.valid:
                self.canvas.itemconfig(rect_id, fill="#b3ecff")  # 有效页
                # 在对应的物理块上显示
                if entry.frame is not None:
                    for (f_rect, f_text, f_no) in self.frame_rects:
                        if f_no == entry.frame:
                            self.canvas.itemconfig(f_rect, fill="#caffca")
                            self.canvas.itemconfig(f_text, text=f"Frame {f_no}\n<-P{page_no}")
            else:
                self.canvas.itemconfig(rect_id, fill="#e0ffff")

    def on_execute(self):
        page_str = self.entry_page_no.get().strip()
        offset_str = self.entry_offset.get().strip()
        op = self.op_var.get()

        if not page_str.isdigit() or not offset_str.isdigit():
            self.log("页号/页内地址必须是整数！")
            return
        page_no = int(page_str)
        offset = int(offset_str)

        msg, replaced_page, loaded_page = self.sim.execute(op, page_no, offset)
        self.log(msg)
        self.update_log_display()

        # 做简单动画
        self.animate_replacement(replaced_page, loaded_page)

    def animate_replacement(self, replaced_page, loaded_page):
        # 被淘汰的页 -> 红色闪烁
        if replaced_page is not None:
            for (rect_id, text_id, p_no) in self.page_rects:
                if p_no == replaced_page:
                    self.flash_color(rect_id, from_color="#e0ffff", to_color="red", duration=ANIMATION_DURATION)

        # 新加载的页 -> 绿色闪烁
        if loaded_page is not None:
            for (rect_id, text_id, p_no) in self.page_rects:
                if p_no == loaded_page:
                    self.flash_color(rect_id, from_color="#e0ffff", to_color="green", duration=ANIMATION_DURATION)

        self.root.after(ANIMATION_DURATION, self.update_canvas_state)

    def flash_color(self, rect_id, from_color, to_color, duration=500):
        half = duration // 2
        self.canvas.itemconfig(rect_id, fill=to_color)
        self.root.after(half, lambda: self.canvas.itemconfig(rect_id, fill=from_color))

    def on_reset(self):
        self.sim.reset()
        self.log("重置模拟器")
        self.update_canvas_state()
        self.update_log_display()

    def log(self, text):
        self.sim.log(text)

    def update_log_display(self):
        self.log_text.delete("1.0", tk.END)
        for line in self.sim.log_lines:
            self.log_text.insert(tk.END, line + "\n")
        self.log_text.see(tk.END)


def main():
    root = tk.Tk()
    app = ConfigWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
