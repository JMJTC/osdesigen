import time

MEMORY_SIZE = 64 * 1024  # 64KB
BLOCK_SIZE = 1024  # 每块 1KB
MAX_BLOCKS = MEMORY_SIZE // BLOCK_SIZE  # 64
MAX_PAGES = 64  # 作业最多可有 64 页(页号范围 0~63)
OFFSET_MAX = BLOCK_SIZE  # 页内地址最大值(0~1023)


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
            msg = f"访问页 {page_no} 超出作业页范围(0~{self.num_pages - 1})"
            self.log(msg)
            return msg, None, None

        # 检查 offset 范围
        if offset < 0 or offset >= BLOCK_SIZE:
            msg = f"页内地址 {offset} 超出范围(0~{BLOCK_SIZE - 1})"
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
