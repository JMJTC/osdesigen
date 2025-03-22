class PagingManager:
    def __init__(self):
        self.jobs = {}
        # 初始化64个内存块（64KB / 1KB per block）
        self.memory = [{'num': i, 'free': True, 'job': None, 'page': None} for i in range(64)]
        self.disk = {}
        self.counter = 0

    def create_job(self, job_id, size=64 * 1024):
        """创建新作业（默认最大64KB）"""
        if job_id in self.jobs:
            return

        pages = size // 1024 + (1 if size % 1024 != 0 else 0)
        page_table = {}
        for i in range(pages):
            page_table[i] = {
                'frame': None,  # 物理块号
                'present': False,  # 是否在内存
                'dirty': False,  # 是否被修改
                'disk_location': f"disk_{job_id}_{i}"  # 磁盘位置
            }
        self.jobs[job_id] = {
            'page_table': page_table,
            'allocated_frames': [],  # 已分配的内存块
            'fifo_queue': []  # FIFO队列
        }

    def access_memory(self, job_id, logical_addr):
        """处理内存访问请求"""
        # 解析逻辑地址
        page = (logical_addr >> 10) & 0x3f  # 取高6位作为页号
        offset = logical_addr & 0x3ff  # 低10位作为页内偏移

        # 自动创建不存在的作业
        if job_id not in self.jobs:
            self.create_job(job_id)

        job = self.jobs[job_id]
        page_table = job['page_table']

        # 初始化返回结果
        result = {
            'physical_addr': None,
            'page_fault': False,
            'replaced_page': None
        }

        # 检查页号是否有效
        if page not in page_table:
            return result

        entry = page_table[page]

        if entry['present']:
            # 页面命中
            frame_num = entry['frame']
            result['physical_addr'] = (frame_num << 10) | offset
        else:
            # 处理缺页中断
            result['page_fault'] = True

            # 尝试分配新帧
            frame = self.allocate_frame(job_id)

            # 需要页面置换
            if frame is None:
                old_frame = self.replace_page(job_id)
                if old_frame is not None:
                    # 处理被替换的页面
                    result['replaced_page'] = old_frame['page']
                    # 如果是脏页需要写回磁盘
                    if page_table[old_frame['page']]['dirty']:
                        self.disk[page_table[old_frame['page']]['disk_location']] = True
                    # 更新旧页表项
                    page_table[old_frame['page']]['present'] = False
                    page_table[old_frame['page']]['frame'] = None
                    frame = old_frame

            # 更新页表
            entry['present'] = True
            entry['frame'] = frame['num']
            # 更新内存块信息
            frame['free'] = False
            frame['job'] = job_id
            frame['page'] = page
            # 计算物理地址
            result['physical_addr'] = (frame['num'] << 10) | offset
            # 更新FIFO队列
            job['fifo_queue'].append(page)

        return result

    def allocate_frame(self, job_id):
        """分配空闲内存块"""
        job = self.jobs[job_id]
        # 在作业分配的内存块中寻找空闲块
        for frame in job['allocated_frames']:
            if frame['free']:
                return frame
        # 分配新内存块
        for frame in self.memory:
            if frame['free']:
                job['allocated_frames'].append(frame)
                return frame
        return None

    def replace_page(self, job_id):
        """执行FIFO页面置换"""
        job = self.jobs[job_id]
        if not job['fifo_queue']:
            return None

        # 获取最早进入的页面
        oldest_page = job['fifo_queue'].pop(0)
        # 获取对应的内存块
        frame_num = job['page_table'][oldest_page]['frame']
        target_frame = next((f for f in job['allocated_frames'] if f['num'] == frame_num), None)

        if target_frame:
            # 重置内存块状态
            target_frame['free'] = True
            target_frame['job'] = None
            target_frame['page'] = None

        return target_frame

    def get_page_table(self, job_id):
        """获取指定作业的页表"""
        if job_id in self.jobs:
            return self.jobs[job_id]['page_table']
        return None