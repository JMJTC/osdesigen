import tkinter as tk
from simulation.paging_simulation import PagingSimulation

ANIMATION_DURATION = 800  # 动画持续时间(毫秒)


# --------------------------
# 动画界面：用户输入(页号、页内地址、操作)后执行
# --------------------------
class PagingAnimationGUI:
    def __init__(self, root, num_pages, allocated_frames_list):
        self.root = root
        self.root.title("请求分页管理模拟")
        self.sim = PagingSimulation(num_pages, allocated_frames_list)

        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 操作输入区
        input_frame = tk.Frame(main_frame)
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

        # 创建左右分栏
        content_frame = tk.Frame(main_frame)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)

        # 左侧动画区域
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 画布
        self.canvas = tk.Canvas(left_frame, width=500, height=300, bg="white")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 右侧页表区域
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # 页表显示区域
        page_table_frame = tk.LabelFrame(right_frame, text="页表")
        page_table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 创建页表显示表格
        self.create_page_table_display(page_table_frame)

        # 日志显示
        log_frame = tk.Frame(main_frame)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        self.log_text = tk.Text(log_frame, width=80, height=6, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, padx=5)
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.btn_reset = tk.Button(log_frame, text="重置", command=self.on_reset)
        self.btn_reset.pack(side=tk.LEFT, padx=10)

        # 可视化数据
        self.frame_rects = []  # (rect_id, text_id, frame_no)
        self.page_rects = []  # (rect_id, text_id, page_no)

        # 初始化显示
        self.draw_static_scene()
        self.update_page_table_display()
        self.update_log_display()

    def create_page_table_display(self, parent):
        # 创建表头
        headers = ["页号", "状态", "物理块号", "修改位"]
        for col, header in enumerate(headers):
            tk.Label(parent, text=header, font=("Arial", 10, "bold"), 
                   relief="ridge", width=12).grid(row=0, column=col, padx=1, pady=1)

        # 创建页表行
        self.page_table_labels = []
        for row in range(self.sim.num_pages):
            row_labels = []
            for col in range(4):
                label = tk.Label(parent, text="", relief="ridge", width=12)
                label.grid(row=row+1, column=col, padx=1, pady=1)
                row_labels.append(label)
            self.page_table_labels.append(row_labels)

    def draw_static_scene(self):
        """绘制静态场景"""
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
        """更新画布状态"""
        # 所有块先恢复"空"状态
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

    def update_page_table_display(self):
        """更新页表显示"""
        for row, entry in enumerate(self.sim.page_table):
            # 页号
            self.page_table_labels[row][0].config(text=f"P{row}")
            
            # 状态
            status = "已加载" if entry.valid else "未加载"
            self.page_table_labels[row][1].config(text=status)
            
            # 物理块号
            frame = str(entry.frame) if entry.frame is not None else "-"
            self.page_table_labels[row][2].config(text=frame)
            
            # 修改位
            modified = "是" if entry.modified else "否"
            self.page_table_labels[row][3].config(text=modified)

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
        self.update_log_display()
        self.update_page_table_display()

        # 执行动画
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
        """颜色闪烁动画"""
        half = duration // 2
        self.canvas.itemconfig(rect_id, fill=to_color)
        self.root.after(half, lambda: self.canvas.itemconfig(rect_id, fill=from_color))

    def on_reset(self):
        self.sim.reset()
        self.log("重置模拟器")
        self.update_canvas_state()
        self.update_page_table_display()
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
