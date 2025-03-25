import tkinter as tk
from simulation.paging_simulation import PagingSimulation

ANIMATION_DURATION = 800  # 动画持续时间(毫秒)


# --------------------------
# 动画界面：用户输入(页号、页内地址、操作)后执行
# --------------------------
class PagingAnimationGUI:
    def __init__(self, root, num_pages, allocated_frames_list):
        # 初始化函数，传入根窗口、页数和已分配的帧列表
        self.root = root
        self.root.title("请求分页管理模拟")
        # 设置窗口标题
        self.sim = PagingSimulation(num_pages, allocated_frames_list)
        # 创建分页模拟对象

        # 操作输入区
        input_frame = tk.Frame(self.root)
        input_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        # 创建输入框框架，并设置位置和填充方式

        tk.Label(input_frame, text="页号：").pack(side=tk.LEFT)
        self.entry_page_no = tk.Entry(input_frame, width=5)
        self.entry_page_no.pack(side=tk.LEFT, padx=2)
        # 创建页号输入框，并设置位置和宽度

        tk.Label(input_frame, text="页内地址：").pack(side=tk.LEFT)
        self.entry_offset = tk.Entry(input_frame, width=6)
        self.entry_offset.pack(side=tk.LEFT, padx=2)
        # 创建页内地址输入框，并设置位置和宽度

        self.op_var = tk.StringVar(value="+")
        ops = ["+", "-", "×", "/", "load", "save"]
        for op in ops:
            r = tk.Radiobutton(input_frame, text=op, variable=self.op_var, value=op)
            r.pack(side=tk.LEFT, padx=2)
        # 创建操作选择框，并设置位置和选项

        self.btn_exec = tk.Button(input_frame, text="执行", command=self.on_execute)
        self.btn_exec.pack(side=tk.LEFT, padx=10)
        # 创建执行按钮，并设置位置和命令

        # 画布
        self.canvas = tk.Canvas(self.root, width=700, height=300, bg="white")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # 创建画布，并设置位置、大小和背景色

        # 日志显示
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.log_text = tk.Text(bottom_frame, width=80, height=8, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, padx=5)
        scrollbar = tk.Scrollbar(bottom_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        # 创建日志显示框，并设置位置、大小、字体和滚动条

        self.btn_reset = tk.Button(bottom_frame, text="重置", command=self.on_reset)
        self.btn_reset.pack(side=tk.LEFT, padx=10)
        # 创建重置按钮，并设置位置和命令

        # 可视化数据
        self.frame_rects = []  # (rect_id, text_id, frame_no)
        self.page_rects = []  # (rect_id, text_id, page_no)
        # 创建可视化数据列表，用于存储帧和页的矩形和文本

        # 绘制静态场景
        self.draw_static_scene()
        self.update_log_display()
        # 绘制静态场景和更新日志显示

    def draw_static_scene(self):
        """
        绘制 allocated_frames_list 对应的方框，以及 num_pages 个“页”。
        """
        self.canvas.delete("all")

        # 绘制分配给作业的物理块
        x0, y0 = 50, 50
        w, h = 60, 40
        gap = 20
        count = 0
        for frame_no in self.sim.allocated_frames_list:
            rect_id = self.canvas.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#f0f0f0")
            text_id = self.canvas.create_text(x0 + w / 2, y0 + h / 2, text=f"Frame {frame_no}", font=("Arial", 10))
            self.frame_rects.append((rect_id, text_id, frame_no))
            x0 += (w + gap)
            count += 1
            if count % 8 == 0:
                x0 = 50
                y0 += (h + gap)

        # 绘制作业的页
        x0, y0 = 50, 100 + 70 * (count / 8)
        w, h = 40, 30
        gap = 10
        count = 0
        for page_no in range(self.sim.num_pages):
            rect_id = self.canvas.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#e0ffff")
            text_id = self.canvas.create_text(x0 + w / 2, y0 + h / 2, text=f"P{page_no}", font=("Arial", 10))
            self.page_rects.append((rect_id, text_id, page_no))
            x0 += (w + gap)
            count += 1
            if count % 8 == 0:
                x0 = 50
                y0 += (h + gap)

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
                if entry.modified:
                    self.canvas.itemconfig(rect_id, fill="#ffebcd")  # 已修改页
                else:
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
        # self.log(msg)
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

    # 定义一个函数，用于在指定时间内将指定矩形的颜色从from_color变为to_color
    def flash_color(self, rect_id, from_color, to_color, duration=500):
        # 计算动画的一半时间
        half = duration // 2
        # 将指定矩形的颜色设置为to_color
        self.canvas.itemconfig(rect_id, fill=to_color)
        # 在动画的一半时间后，将指定矩形的颜色设置为from_color
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


if __name__ == "__main__":
    print("hello,我们来模拟一下分页系统吧！")
