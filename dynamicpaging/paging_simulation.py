import time

MEMORY_SIZE = 64 * 1024    # 64KB
BLOCK_SIZE = 1024          # 每块 1KB
MAX_BLOCKS = MEMORY_SIZE // BLOCK_SIZE  # 64
MAX_PAGES = 64             # 作业最多可有 64 页(页号范围 0~63)
OFFSET_MAX = BLOCK_SIZE    # 页内地址最大值(0~1023)
ANIMATION_DURATION = 800   # 动画持续时间(毫秒)

from page_table import PageTableEntry

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
        self.allocated_frames_list = allocated_frames_list
        self.page_table = [PageTableEntry() for _ in range(num_pages)]
        self.fifo_queue = []
        self.used_frames = set()

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
        log_info = ""
        replaced_page = None
        loaded_page = None
        # 这里可以添加具体的执行逻辑
        return log_info, replaced_page, loaded_page

    def find_free_frame(self):
        """
        在 allocated_frames_list 中找一个尚未使用的帧号返回(选最小或第一个可用)。
        """
        for frame in self.allocated_frames_list:
            if frame not in self.used_frames:
                return frame
        return None

    def log(self, text):
        print(text)

    def get_page_table_snapshot(self):
        """返回当前页表信息，用于GUI显示。每项为 (页号, valid, frame, modified)。"""
        snapshot = []
        for i, entry in enumerate(self.page_table):
            snapshot.append((i, entry.valid, entry.frame, entry.modified))
        return snapshot

    def reset(self):
        """重置模拟状态：全部无效，FIFO 队列清空，used_frames 清空。"""
        for entry in self.page_table:
            entry.valid = False
            entry.frame = None
            entry.modified = False
        self.fifo_queue = []
        self.used_frames = set()