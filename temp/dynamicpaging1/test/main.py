import tkinter as tk
from tkinter import ttk, messagebox
import time
import re

# 常量定义
MEMORY_SIZE = 64 * 1024       # 64KB
BLOCK_SIZE = 1024             # 每块1024字节
OFFSET_MAX = BLOCK_SIZE

def format_disk_pos(page):
    # 可自定义磁盘位置格式，本例采用“Dxxx”
    return f"D{page:03d}"

class PagingSimulation:
    def __init__(self, instructions, allocated_frames, init_loaded_pages):
        """
        instructions: list of (序号, 操作, 页号, 页内地址)
        allocated_frames: list of int，作业分配的内存块（物理帧号）
        init_loaded_pages: list of int，初始加载到内存的页号，
                           按顺序分配给 allocated_frames 前部分帧
        """
        self.instructions = instructions
        # 构造页表：页号范围根据指令中出现的最大页号决定
        max_page = max(inst[2] for inst in instructions) if instructions else 0
        self.page_table = {}
        for p in range(max_page + 1):
            # 若p在初始加载列表中，则分配对应的帧（按输入顺序）
            if p in init_loaded_pages:
                idx = init_loaded_pages.index(p)
                # 若用户输入的初始加载页数多于分配的帧数，则超出部分无法加载
                if idx < len(allocated_frames):
                    frame = allocated_frames[idx]
                    valid = True
                else:
                    frame = None
                    valid = False
            else:
                frame = None
                valid = False
            self.page_table[p] = {'valid': valid, 'frame': frame, 'modified': False, 'disk_pos': format_disk_pos(p)}
        
        # 记录作业分配的内存块列表
        self.allocated_frames = allocated_frames.copy()
        # 初始化：在内存中的页号到帧号的映射（仅初始加载的页面）
        self.frame_usage = {p: self.page_table[p]['frame'] for p in init_loaded_pages if self.page_table[p]['frame'] is not None}
        # FIFO 队列：记录已加载的页号，顺序按照初始加载的顺序
        self.fifo_queue = init_loaded_pages.copy()
        # 记录模拟日志，用于显示
        self.log_lines = []
        # 当前指令索引
        self.current_index = 0

    def process_next_instruction(self):
        if self.current_index >= len(self.instructions):
            self.log("所有指令执行完毕。")
            return False

        seq, op, page_no, offset = self.instructions[self.current_index]
        log_info = f"【指令 {seq}】: 操作 {op}, 页号 {page_no}, 页内地址 {offset:03d} -> "
        fault_occurred = False

        if page_no not in self.page_table:
            self.log(f"错误：页号 {page_no} 不存在！")
            self.current_index += 1
            return True

        entry = self.page_table[page_no]
        if entry['valid']:
            # 页在内存中，直接计算物理地址
            frame = entry['frame']
            phys_addr = frame * BLOCK_SIZE + offset
            log_info += f"物理地址 = {phys_addr}；不缺页。"
        else:
            # 缺页中断发生
            fault_occurred = True
            log_info += "缺页中断，"
            # 判断在该作业分得的内存块中是否有空闲（即在 allocated_frames 中未被占用的）
            free_frames = [f for f in self.allocated_frames if f not in self.frame_usage.values()]
            if free_frames:
                # 若有空闲帧，则使用空闲帧
                frame = free_frames[0]
                log_info += f"空闲帧 {frame}。"
            else:
                # 没有空闲帧，则按 FIFO 从本作业中淘汰一个页面
                evict_page = self.fifo_queue.pop(0)
                evicted_frame = self.frame_usage.pop(evict_page)
                self.page_table[evict_page]['valid'] = False
                self.page_table[evict_page]['frame'] = None
                log_info += f"淘汰页 {evict_page}（占用帧 {evicted_frame}）；使用该帧。"
                frame = evicted_frame

            # 装入缺页，将页面 page_no 放入 frame
            self.page_table[page_no]['valid'] = True
            self.page_table[page_no]['frame'] = frame
            # 根据操作设置修改标志（这里只对 "存(save)" 操作置1，其它操作置0，可按需要扩展）
            if op.strip() == '存(save)':
                self.page_table[page_no]['modified'] = True
            else:
                self.page_table[page_no]['modified'] = False
            # 加入 FIFO 队列和帧使用记录
            self.fifo_queue.append(page_no)
            self.frame_usage[page_no] = frame
            # 计算物理地址
            phys_addr = frame * BLOCK_SIZE + offset
            log_info += f"计算物理地址 = {phys_addr}。"

        self.log(log_info)
        self.log_page_table()
        self.current_index += 1
        return True

    def log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.log_lines.append(f"[{timestamp}] {text}")

    def log_page_table(self):
        header = "当前页表状态：\n页号\t有效\t帧号\t修改\t磁盘位置"
        lines = [header]
        for p in sorted(self.page_table.keys()):
            entry = self.page_table[p]
            valid = "1" if entry['valid'] else "0"
            frame = str(entry['frame']) if entry['frame'] is not None else "-"
            modified = "1" if entry['modified'] else "0"
            disk = entry['disk_pos']
            lines.append(f"{p}\t{valid}\t{frame}\t{modified}\t{disk}")
        self.log("\n".join(lines))

    def reset(self):
        # 重新初始化模拟状态：将所有指令位置归零，重建页表、FIFO 队列和帧使用记录
        # 注意：allocated_frames 和初始加载页保持不变
        init_loaded_pages = [p for p in self.fifo_queue if p in self.frame_usage]  # 原先初始加载的页号
        max_page = max(self.page_table.keys())
        for p in range(max_page + 1):
            if p in init_loaded_pages:
                idx = init_loaded_pages.index(p)
                if idx < len(self.allocated_frames):
                    frame = self.allocated_frames[idx]
                    self.page_table[p] = {'valid': True, 'frame': frame, 'modified': False, 'disk_pos': format_disk_pos(p)}
                else:
                    self.page_table[p] = {'valid': False, 'frame': None, 'modified': False, 'disk_pos': format_disk_pos(p)}
            else:
                self.page_table[p] = {'valid': False, 'frame': None, 'modified': False, 'disk_pos': format_disk_pos(p)}
        self.fifo_queue = init_loaded_pages.copy()
        self.frame_usage = {p: self.page_table[p]['frame'] for p in init_loaded_pages if self.page_table[p]['frame'] is not None}
        self.log_lines = []
        self.current_index = 0
        self.log("模拟状态已重置。")
        self.log_page_table()


class PagingGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("动态分页管理模拟")
        # 使用两个Frame：配置Frame 和 模拟Frame
        self.config_frame = tk.Frame(self.root)
        self.sim_frame = tk.Frame(self.root)
        self.simulation = None  # 后续保存 PagingSimulation 对象
        self.create_config_frame()
        self.config_frame.pack(fill=tk.BOTH, expand=True)

    def create_config_frame(self):
        # 配置界面，允许用户输入：
        # 1. 作业分配的内存块（逗号分隔，如：5,8,9,1）
        # 2. 初始加载的页号（逗号分隔，如：0,1,2,3）
        # 3. 指令（每行格式：操作,页号,页内地址）
        lbl_title = tk.Label(self.config_frame, text="动态分页管理模拟配置", font=("Arial", 14))
        lbl_title.pack(pady=10)

        # 输入作业分配的内存块
        frame_alloc = tk.Frame(self.config_frame)
        frame_alloc.pack(pady=5, fill=tk.X, padx=20)
        lbl_alloc = tk.Label(frame_alloc, text="作业分配的内存块（逗号分隔）：")
        lbl_alloc.pack(side=tk.LEFT)
        self.entry_alloc = tk.Entry(frame_alloc, width=30)
        self.entry_alloc.pack(side=tk.LEFT, padx=5)
        self.entry_alloc.insert(0, "5,8,9,1")  # 默认值

        # 输入初始加载的页号
        frame_init = tk.Frame(self.config_frame)
        frame_init.pack(pady=5, fill=tk.X, padx=20)
        lbl_init = tk.Label(frame_init, text="初始加载的页号（逗号分隔）：")
        lbl_init.pack(side=tk.LEFT)
        self.entry_init = tk.Entry(frame_init, width=30)
        self.entry_init.pack(side=tk.LEFT, padx=5)
        self.entry_init.insert(0, "0,1,2,3")  # 默认值

        # 输入指令
        lbl_instr = tk.Label(self.config_frame, text="请输入指令（每行格式：操作,页号,页内地址）：")
        lbl_instr.pack(pady=5)
        self.text_instr = tk.Text(self.config_frame, width=60, height=10)
        self.text_instr.pack(padx=20)
        # 默认指令示例
        default_instructions = (
            "+,0,72\n"
            "/,1,50\n"
            "╳,2,15\n"
            "存(save),3,26\n"
            "取(load),0,56\n"
            "—,6,40\n"
            "+,4,56\n"
            "—,5,23\n"
            "存(save),1,37\n"
            "+,2,78\n"
            "—,4,1\n"
            "存(save),6,86\n"
        )
        self.text_instr.insert(tk.END, default_instructions)

        # 开始模拟按钮
        btn_start = tk.Button(self.config_frame, text="开始模拟", command=self.start_simulation)
        btn_start.pack(pady=10)

    def start_simulation(self):
        # 从输入中解析 allocated_frames, init_loaded_pages 和 instructions
        alloc_text = self.entry_alloc.get().strip()
        init_text = self.entry_init.get().strip()
        instr_text = self.text_instr.get("1.0", tk.END).strip()

        try:
            allocated_frames = [int(x.strip()) for x in alloc_text.split(",") if x.strip() != ""]
            init_loaded_pages = [int(x.strip()) for x in init_text.split(",") if x.strip() != ""]
        except Exception as e:
            messagebox.showerror("输入错误", "内存块或初始加载页号格式错误，请输入逗号分隔的整数。")
            return

        if not allocated_frames:
            messagebox.showerror("输入错误", "请至少输入一个内存块号。")
            return

        # 解析指令
        instructions = []
        lines = instr_text.splitlines()
        seq = 1
        pattern = re.compile(r'^\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*$')
        for line in lines:
            if line.strip() == "":
                continue
            m = pattern.match(line)
            if not m:
                messagebox.showerror("输入错误", f"指令格式错误：{line}")
                return
            op, page_str, offset_str = m.groups()
            try:
                page_no = int(page_str)
                offset = int(offset_str)
            except:
                messagebox.showerror("输入错误", f"页号或页内地址必须为整数：{line}")
                return
            # 检查 offset 是否超过范围
            if offset < 0 or offset >= BLOCK_SIZE:
                messagebox.showerror("输入错误", f"页内地址必须在0-{BLOCK_SIZE - 1}之间：{line}")
                return
            instructions.append((seq, op.strip(), page_no, offset))
            seq += 1

        # 创建 PagingSimulation 对象
        self.simulation = PagingSimulation(instructions, allocated_frames, init_loaded_pages)
        # 切换到模拟界面
        self.config_frame.forget()
        self.create_sim_frame()
        self.sim_frame.pack(fill=tk.BOTH, expand=True)

    def create_sim_frame(self):
        # 模拟界面，显示日志及控制按钮
        top_frame = tk.Frame(self.sim_frame)
        top_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        lbl_title = tk.Label(top_frame, text="动态分页管理模拟运行", font=("Arial", 14))
        lbl_title.pack(pady=5)

        # 日志显示区
        self.log_text = tk.Text(top_frame, width=80, height=20, font=("Consolas", 10))
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 控制按钮区域
        btn_frame = tk.Frame(self.sim_frame)
        btn_frame.pack(pady=5)
        self.next_btn = tk.Button(btn_frame, text="下一步", command=self.next_step)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        self.run_btn = tk.Button(btn_frame, text="自动运行", command=self.auto_run)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        self.reset_btn = tk.Button(btn_frame, text="重置", command=self.reset_simulation)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        self.back_btn = tk.Button(btn_frame, text="返回配置", command=self.back_to_config)
        self.back_btn.pack(side=tk.LEFT, padx=5)

        # 初始化日志显示
        self.update_log_display()

    def next_step(self):
        if self.simulation.process_next_instruction():
            self.update_log_display()
        else:
            self.next_btn.config(state=tk.DISABLED)
            self.run_btn.config(state=tk.DISABLED)

    def auto_run(self):
        if self.simulation.process_next_instruction():
            self.update_log_display()
            self.sim_frame.after(1000, self.auto_run)
        else:
            self.next_btn.config(state=tk.DISABLED)
            self.run_btn.config(state=tk.DISABLED)

    def reset_simulation(self):
        if self.simulation:
            self.simulation.reset()
            self.update_log_display()
            self.next_btn.config(state=tk.NORMAL)
            self.run_btn.config(state=tk.NORMAL)

    def back_to_config(self):
        # 返回配置界面
        self.sim_frame.forget()
        self.config_frame.pack(fill=tk.BOTH, expand=True)

    def update_log_display(self):
        self.log_text.delete("1.0", tk.END)
        for line in self.simulation.log_lines:
            self.log_text.insert(tk.END, line + "\n")
        self.log_text.see(tk.END)

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    gui = PagingGUI()
    gui.run()
