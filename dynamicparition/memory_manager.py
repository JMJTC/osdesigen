class MemoryManager:
    def __init__(self, total_memory):
        self.total_memory = total_memory
        self.free_blocks = [{'start': 0, 'size': total_memory}]
        self.allocated_blocks = {}
        self.next_process_id = 1
        self.history = []  # 操作历史
        self.current_history_index = -1

    # 获取内存使用率
    def get_memory_usage(self):
        used_memory = sum(block['size'] for block in self.allocated_blocks.values())
        return (used_memory / self.total_memory) * 100

    # 获取内存碎片化程度
    def get_fragmentation(self):
        # 如果没有空闲块，则返回0
        if not self.free_blocks:
            return 0
        # 计算所有空闲块的总大小
        total_free = sum(block['size'] for block in self.free_blocks)
        # 计算最大的空闲块大小
        max_free = max(block['size'] for block in self.free_blocks)
        # 返回最大空闲块大小与总空闲块大小的比例差值，乘以100，如果总空闲块大小大于0，否则返回0
        # 内存碎片率 FR 可以用公式 \(FR = (T - M) / T \times 100\%\) 来计算。
        return ((total_free - max_free) / total_free) * 100 if total_free > 0 else 0

    # 保存当前状态
    def save_state(self):
        self.current_history_index += 1
        self.history = self.history[:self.current_history_index]
        self.history.append({
            'free_blocks': self.free_blocks.copy(),
            'allocated_blocks': self.allocated_blocks.copy(),
            'next_process_id': self.next_process_id
        })

    # 撤销操作
    def undo(self):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            state = self.history[self.current_history_index]
            self.free_blocks = state['free_blocks'].copy()
            self.allocated_blocks = state['allocated_blocks'].copy()
            self.next_process_id = state['next_process_id']
            return True
        return False

    # 重做操作
    def redo(self):
        if self.current_history_index < len(self.history) - 1:
            self.current_history_index += 1
            state = self.history[self.current_history_index]
            self.free_blocks = state['free_blocks'].copy()
            self.allocated_blocks = state['allocated_blocks'].copy()
            self.next_process_id = state['next_process_id']
            return True
        return False

    # 分配内存
    # 可用策略模式优化
    def allocate(self, size, algorithm):
        self.save_state()
        if algorithm == 'first_fit':
            return self._allocate_first_fit(size)
        elif algorithm == 'best_fit':
            return self._allocate_best_fit(size)
        elif algorithm == 'worst_fit':
            return self._allocate_worst_fit(size)
        return None

    # 使用首次适应算法分配内存
    def _allocate_first_fit(self, size):
        # 遍历free_blocks列表，查找第一个大小大于等于size的空闲块
        for i, block in enumerate(self.free_blocks):
            if block['size'] >= size:
                # 如果找到，则调用_split_block函数，将空闲块分割成size大小的块，并返回
                return self._split_block(i, block, size)
        # 如果没有找到，则返回None
        return None

    # 使用最佳适应算法分配内存
    def _allocate_best_fit(self, size):
        # 初始化最佳索引和最小大小
        best_idx = -1
        min_size = float('inf')
        # 遍历所有空闲块
        for i, block in enumerate(self.free_blocks):
            # 如果当前块的大小满足条件且小于最小大小，则更新最佳索引和最小大小
            if size <= block['size'] < min_size:
                best_idx = i
                min_size = block['size']
        # 如果没有找到合适的块，则返回None
        if best_idx == -1:
            return None
        # 否则，调用_split_block方法分割块
        return self._split_block(best_idx, self.free_blocks[best_idx], size)

    # 使用最差适应算法分配内存
    def _allocate_worst_fit(self, size):
        # 如果没有空闲块，则返回None
        if not self.free_blocks:
            return None
        # 找到空闲块中大小最大的块
        worst_idx = max(range(len(self.free_blocks)),
                        key=lambda i: self.free_blocks[i]['size'])
        # 获取该块
        block = self.free_blocks[worst_idx]
        # 如果该块的大小小于请求的大小，则返回None
        if block['size'] < size:
            return None
        # 否则，将块分割成请求的大小，并返回分割后的块
        return self._split_block(worst_idx, block, size)

    # 分割内存块
    def _split_block(self, index, block, size):
        # 计算新块的起始位置
        new_start = block['start'] + size
        # 计算新块的大小
        new_size = block['size'] - size
        # 删除原块
        del self.free_blocks[index]
        # 如果新块大小大于0，则将新块插入到原块的位置
        if new_size > 0:
            self.free_blocks.insert(index, {'start': new_start, 'size': new_size})
        # 获取下一个进程ID
        pid = self.next_process_id
        # 将原块分配给进程
        self.allocated_blocks[pid] = {'start': block['start'], 'size': size}
        # 进程ID加1
        self.next_process_id += 1
        # 返回进程ID
        return pid

    # 释放内存
    def deallocate(self, pid):
        # 保存当前状态
        self.save_state()
        # 如果pid不在已分配的块中，则返回False
        if pid not in self.allocated_blocks:
            return False
        # 获取pid对应的块
        block = self.allocated_blocks[pid]
        # 将该块添加到空闲块中
        self.free_blocks.append({'start': block['start'], 'size': block['size']})
        # 从已分配的块中删除该pid
        del self.allocated_blocks[pid]
        # 合并空闲块
        self._merge_blocks()
        # 返回True
        return True

    # 合并相邻的内存块
    def _merge_blocks(self):
        # 将free_blocks按照start属性进行排序
        self.free_blocks.sort(key=lambda x: x['start'])
        # 初始化i为0
        i = 0
        # 当i小于free_blocks的长度减1时，执行循环
        while i < len(self.free_blocks) - 1:
            # 获取当前块
            current = self.free_blocks[i]
            # 获取下一个块
            next_block = self.free_blocks[i + 1]
            # 如果当前块的start属性加上size属性等于下一个块的start属性
            if current['start'] + current['size'] == next_block['start']:
                # 将当前块的size属性加上下一个块的size属性
                current['size'] += next_block['size']
                # 删除下一个块
                del self.free_blocks[i + 1]
            # 否则，i加1
            else:
                i += 1
