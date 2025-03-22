import tkinter as tk
from tkinter import ttk, messagebox
import time

# --------------------------
# 全局常量
# --------------------------
MEMORY_SIZE = 64 * 1024   # 64KB
BLOCK_SIZE = 1024         # 每块 1KB
MAX_BLOCKS = MEMORY_SIZE // BLOCK_SIZE  # 64
MAX_PAGES = 64            # 作业最大可有 64 页 (0~63)
OFFSET_MAX = BLOCK_SIZE   # 页内地址最大值(0~1023)
ANIMATION_DURATION = 800  # 动画持续时间(毫秒)


class PageTableEntry:
    """
    页表项：valid、frame、modified
    注：在实际系统中还可能记录磁盘位置、访问时间等，这里简化。
    """
    def __init__(self, valid=False, frame=None, modified=False):
        self.valid = valid
        self.frame = frame
        self.modified = modified


class PagingSimulation:
    """
    管理页表、内存块，以及执行指令时的页面调度逻辑。
    使用 FIFO 在分配给作业的若干块中进行替换。
    """
    def __init__(self, num_pages, allocated_frames):
        """
        :param num_pages: 作业拥有的页数 (1~64)
        :param allocated_frames: 给作业分配的物理块数量 (1~64)
        """
        self.num_pages = num_pages
        self.allocated_frames = allocated_frames
        # 初始化页表(全部 invalid)
        self.page_table = [PageTableEntry() for _ in range(num_pages)]

        # FIFO 队列，存放当前在内存中的页号(先进先出)
        self.fifo_queue = []

        # 为简化演示，假设作业初始时没有任何页在内存
        # (若想初始时装入前 N 页，可自行在此修改)
        # self.page_table[0].valid = True; self.page_table[0].frame = 0; ...
        # self.fifo_queue.append(0); ...

        # 记录已经使用的帧号(真实系统中应有可用帧列表，这里仅示例)
        self.used_frames = set()

        # 日志
        self.log_lines = []
        self.log(f"初始化：作业共有 {num_pages} 页，分配 {allocated_frames} 个物理块。")

    def execute(self, op, page_no, offset):
        """
        执行一次访问：
          :param op: 操作类型 (字符串，如 +, -, ×, /, load, save)
          :param page_no: 访问的页号
          :param offset: 页内地址
        :return: (log_info, replaced_page, loaded_page)
                 - log_info: 字符串日志
                 - replaced_page: 若发生替换，返回被淘汰的页号；否则 None
                 - loaded_page: 若发生装载，返回装载的页号；否则 None
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
            # 缺页
            msg = f"访问页 {page_no} -> 缺页中断, "
            if len(self.fifo_queue) < self.allocated_frames:
                # 还有空闲帧(或可用位置)
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

                # 分配给 page_no
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
        简化：在 0 ~ (MAX_BLOCKS-1)=63 范围里找一个不在 used_frames 里的最小编号返回。
        真实系统可能要根据内存分配给本作业的块列表来找，这里为演示做最简处理。
        """
        for f in range(MAX_BLOCKS):
            if f not in self.used_frames:
                return f
        # 理论上不会走到这里，因为 allocated_frames <= 64
        return 0

    def log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {text}"
        self.log_lines.append(line)

    def get_page_table_snapshot(self):
        """
        返回当前页表信息，用于 GUI 显示。
        每项为 (页号, valid, frame, modified)
        """
        data = []
        for i, e in enumerate(self.page_table):
            valid = 1 if e.valid else 0
            frame = e.frame if e.frame is not None else "-"
            modified = 1 if e.modified else 0
            data.append((i, valid, frame, modified))
        return data

    def reset(self):
        """重置模拟状态：清空页表和 FIFO 队列，保留 num_pages & allocated_frames 不变。"""
        self.page_table = [PageTableEntry() for _ in range(self.num_pages)]
        self.fifo_queue = []
        self.used_frames = set()
        self.log_lines = []
        self.log("模拟状态已重置。")


# --------------------------
# GUI 界面
# --------------------------
class ConfigWindow:
    """
    启动时的配置窗口，让用户输入：
      - 作业的页数 (1~64)
      - 分配给该作业的物理块数量 (1~64)
    点击“开始模拟”后，进入 PagingAnimationGUI。
    """
    def __init__(self, root):
        self.root = root
        self.root.title("请求分页模拟 - 配置")
        self.create_widgets()

        # 在这里先隐藏主窗口，等用户点开始模拟后再显示
        # 也可以不隐藏，直接在同一个窗口切换 Frame
        self.sim_window = None

    def create_widgets(self):
        frm = tk.Frame(self.root)
        frm.pack(padx=20, pady=20)

        tk.Label(frm, text="作业页数(1~64):").grid(row=0, column=0, pady=5, sticky=tk.E)
        self.entry_pages = tk.Entry(frm, width=10)
        self.entry_pages.grid(row=0, column=1, pady=5, sticky=tk.W)
        self.entry_pages.insert(0, "8")  # 默认8页

        tk.Label(frm, text="分配的物理块数(1~64):").grid(row=1, column=0, pady=5, sticky=tk.E)
        self.entry_frames = tk.Entry(frm, width=10)
        self.entry_frames.grid(row=1, column=1, pady=5, sticky=tk.W)
        self.entry_frames.insert(0, "4")  # 默认4块

        btn_start = tk.Button(frm, text="开始模拟", command=self.start_sim)
        btn_start.grid(row=2, column=0, columnspan=2, pady=15)

    def start_sim(self):
        pages_str = self.entry_pages.get().strip()
        frames_str = self.entry_frames.get().strip()
        if not (pages_str.isdigit() and frames_str.isdigit()):
            messagebox.showerror("输入错误", "请输入有效的整数！")
            return
        num_pages = int(pages_str)
        allocated_frames = int(frames_str)
        if not (1 <= num_pages <= MAX_PAGES):
            messagebox.showerror("输入错误", f"作业页数必须在 1~{MAX_PAGES} 之间！")
            return
        if not (1 <= allocated_frames <= MAX_BLOCKS):
            messagebox.showerror("输入错误", f"物理块数必须在 1~{MAX_BLOCKS} 之间！")
            return

        # 创建新的窗口进行模拟
        self.sim_window = tk.Toplevel(self.root)
        self.sim_gui = PagingAnimationGUI(self.sim_window, num_pages, allocated_frames)


class PagingAnimationGUI:
    """
    交互式动画界面：
      - 用户输入“页号”“页内地址”和“操作类型”点击执行
      - 画布上显示(简化的)内存块 & 页表，执行后若缺页/替换会闪烁动画
      - 下方日志显示
      - “重置”按钮可恢复最初状态
    """
    def __init__(self, root, num_pages, allocated_frames):
        self.root = root
        self.root.title("请求分页管理模拟 - 交互动画")
        self.sim = PagingSimulation(num_pages, allocated_frames)

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

        # 下方：日志显示 + 重置按钮
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.log_text = tk.Text(bottom_frame, width=80, height=8, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, padx=5)
        scrollbar = tk.Scrollbar(bottom_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.btn_reset = tk.Button(bottom_frame, text="重置", command=self.on_reset)
        self.btn_reset.pack(side=tk.LEFT, padx=10)

        # 画布中绘制
        self.frame_rects = []  # 用来存储“内存块”对应的矩形/文本
        self.page_rects = []   # 用来存储“页表”对应的矩形/文本

        # 先画静态场景(多少块、多少页)
        self.draw_static_scene()
        self.update_log_display()

    def draw_static_scene(self):
        """
        绘制简化示意：在 canvas 上画出 allocated_frames 个“帧”方框，
        以及 num_pages 个“页”方框。
        """
        self.canvas.delete("all")
        # 先画内存帧(allocated_frames)
        x0, y0 = 50, 50
        w, h = 80, 40
        gap = 20
        for i in range(self.sim.allocated_frames):
            rect_id = self.canvas.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#f0f0f0")
            text_id = self.canvas.create_text(x0 + w/2, y0 + h/2, text=f"Frame {i}", font=("Arial", 10))
            self.frame_rects.append((rect_id, text_id))
            x0 += (w + gap)

        # 再画页( num_pages )，示例中尽量一行放下
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
        根据 self.sim 的页表状态，更新 Canvas 中各个方框的显示
        """
        # 先将所有 Frame 标记为“空”颜色
        for i, (rect_id, text_id) in enumerate(self.frame_rects):
            self.canvas.itemconfig(rect_id, fill="#f0f0f0")
            self.canvas.itemconfig(text_id, text=f"Frame {i}")

        # 再更新页颜色
        for page_no, entry in enumerate(self.sim.page_table):
            rect_id, text_id = self.page_rects[page_no]
            if entry.valid:
                self.canvas.itemconfig(rect_id, fill="#b3ecff")  # 有效页
                if entry.frame is not None:
                    # 如果 frame < allocated_frames，表示映射到我们画的那些方框中
                    if entry.frame < len(self.frame_rects):
                        f_rect, f_text = self.frame_rects[entry.frame]
                        self.canvas.itemconfig(f_rect, fill="#caffca")
                        self.canvas.itemconfig(f_text, text=f"F{entry.frame}\n<-P{page_no}")
            else:
                self.canvas.itemconfig(rect_id, fill="#e0ffff")  # 无效页

    def on_execute(self):
        """用户点击执行后，读取输入并模拟一次访问"""
        page_str = self.entry_page_no.get().strip()
        offset_str = self.entry_offset.get().strip()
        op = self.op_var.get()

        # 校验输入
        if not page_str.isdigit() or not offset_str.isdigit():
            self.log("页号/偏移量必须是整数！")
            return
        page_no = int(page_str)
        offset = int(offset_str)

        msg, replaced_page, loaded_page = self.sim.execute(op, page_no, offset)
        self.log(msg)
        self.update_log_display()
        # 执行后动画
        self.animate_replacement(replaced_page, loaded_page)

    def animate_replacement(self, replaced_page, loaded_page):
        """
        若发生替换/加载，就高亮闪烁
        """
        # 被淘汰的页 -> 红色闪烁
        if replaced_page is not None:
            rect_id, _ = self.page_rects[replaced_page]
            self.flash_color(rect_id, from_color="#e0ffff", to_color="red", duration=ANIMATION_DURATION)

        # 新加载的页 -> 绿色闪烁
        if loaded_page is not None:
            rect_id, _ = self.page_rects[loaded_page]
            self.flash_color(rect_id, from_color="#e0ffff", to_color="green", duration=ANIMATION_DURATION)

        # 等动画结束再更新整体状态
        self.root.after(ANIMATION_DURATION, self.update_canvas_state)

    def flash_color(self, rect_id, from_color, to_color, duration=500):
        """
        将指定矩形从 from_color 闪烁到 to_color，再闪回，持续 duration 毫秒。
        """
        half = duration // 2
        self.canvas.itemconfig(rect_id, fill=to_color)
        self.root.after(half, lambda: self.canvas.itemconfig(rect_id, fill=from_color))

    def on_reset(self):
        self.sim.reset()
        self.log("重置模拟器")
        self.update_canvas_state()
        self.update_log_display()

    def log(self, text):
        """写入日志"""
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
