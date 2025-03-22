import tkinter as tk
from tkinter import ttk, messagebox
from paging_simulation import PagingSimulation

class PagingAnimationGUI:
    def __init__(self, root, num_pages, allocated_frames_list):
        self.root = root
        self.num_pages = num_pages
        self.allocated_frames_list = allocated_frames_list
        self.sim = PagingSimulation(num_pages, allocated_frames_list)
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack()
        self.draw_static_scene()
        self.create_input_widgets()

    def draw_static_scene(self):
        """
        绘制 allocated_frames_list 对应的方框，以及 num_pages 个“页”。
        """
        pass

    def update_canvas_state(self):
        """
        根据 self.sim 的页表状态，更新 Canvas 中各个方框的显示。
        """
        pass

    def create_input_widgets(self):
        self.page_no_label = ttk.Label(self.root, text="页号:")
        self.page_no_label.pack()
        self.page_no_entry = ttk.Entry(self.root)
        self.page_no_entry.pack()

        self.offset_label = ttk.Label(self.root, text="页内地址:")
        self.offset_label.pack()
        self.offset_entry = ttk.Entry(self.root)
        self.offset_entry.pack()

        self.op_label = ttk.Label(self.root, text="操作:")
        self.op_label.pack()
        self.op_entry = ttk.Entry(self.root)
        self.op_entry.pack()

        self.execute_button = ttk.Button(self.root, text="执行", command=self.on_execute)
        self.execute_button.pack()

        self.reset_button = ttk.Button(self.root, text="重置", command=self.on_reset)
        self.reset_button.pack()

    def on_execute(self):
        try:
            page_no = int(self.page_no_entry.get())
            offset = int(self.offset_entry.get())
            op = self.op_entry.get()
            log_info, replaced_page, loaded_page = self.sim.execute(op, page_no, offset)
            self.log(log_info)
            if replaced_page is not None:
                self.animate_replacement(replaced_page, loaded_page)
            self.update_canvas_state()
            self.update_log_display()
        except ValueError:
            messagebox.showerror("错误", "输入格式错误，请输入有效的整数")

    def animate_replacement(self, replaced_page, loaded_page):
        # 被淘汰的页 -> 红色闪烁
        pass

    def flash_color(self, rect_id, from_color, to_color, duration=500):
        pass

    def on_reset(self):
        self.sim.reset()
        self.update_canvas_state()
        self.update_log_display()

    def log(self, text):
        self.sim.log(text)

    def update_log_display(self):
        pass