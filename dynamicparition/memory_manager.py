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
        if not self.free_blocks:
            return 0
        total_free = sum(block['size'] for block in self.free_blocks)
        max_free = max(block['size'] for block in self.free_blocks)
        return ((max_free / total_free) - 1) * 100 if total_free > 0 else 0

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
        for i, block in enumerate(self.free_blocks):
            if block['size'] >= size:
                return self._split_block(i, block, size)
        return None

    # 使用最佳适应算法分配内存
    def _allocate_best_fit(self, size):
        best_idx = -1
        min_size = float('inf')
        for i, block in enumerate(self.free_blocks):
            if size <= block['size'] < min_size:
                best_idx = i
                min_size = block['size']
        if best_idx == -1:
            return None
        return self._split_block(best_idx, self.free_blocks[best_idx], size)

    # 使用最差适应算法分配内存
    def _allocate_worst_fit(self, size):
        if not self.free_blocks:
            return None
        worst_idx = max(range(len(self.free_blocks)),
                        key=lambda i: self.free_blocks[i]['size'])
        block = self.free_blocks[worst_idx]
        if block['size'] < size:
            return None
        return self._split_block(worst_idx, block, size)

    # 分割内存块
    def _split_block(self, index, block, size):
        new_start = block['start'] + size
        new_size = block['size'] - size
        del self.free_blocks[index]
        if new_size > 0:
            self.free_blocks.insert(index, {'start': new_start, 'size': new_size})
        pid = self.next_process_id
        self.allocated_blocks[pid] = {'start': block['start'], 'size': size}
        self.next_process_id += 1
        return pid

    # 释放内存
    def deallocate(self, pid):
        self.save_state()
        if pid not in self.allocated_blocks:
            return False
        block = self.allocated_blocks[pid]
        self.free_blocks.append({'start': block['start'], 'size': block['size']})
        del self.allocated_blocks[pid]
        self._merge_blocks()
        return True

    # 合并相邻的内存块
    def _merge_blocks(self):
        self.free_blocks.sort(key=lambda x: x['start'])
        i = 0
        while i < len(self.free_blocks) - 1:
            current = self.free_blocks[i]
            next_block = self.free_blocks[i + 1]
            if current['start'] + current['size'] == next_block['start']:
                current['size'] += next_block['size']
                del self.free_blocks[i + 1]
            else:
                i += 1
