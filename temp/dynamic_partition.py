# dynamic_partition.py
class DynamicPartitionManager:
    def __init__(self):
        self.memory = []
        self.allocations = {}

    def initialize_memory(self, total_size):
        self.memory = [{
            'start': 0,
            'size': total_size,
            'free': True,
            'pid': None
        }]
        self.allocations = {}

    def allocate(self, pid, size, algorithm):
        if pid in self.allocations:
            return False

        index = self.find_free_block(size, algorithm)
        if index is None:
            return False

        block = self.memory[index]
        if block['size'] == size:
            block['free'] = False
            block['pid'] = pid
        else:
            new_block = {
                'start': block['start'] + size,
                'size': block['size'] - size,
                'free': True,
                'pid': None
            }
            self.memory[index:index + 1] = [
                {'start': block['start'], 'size': size, 'free': False, 'pid': pid},
                new_block
            ]

        self.allocations[pid] = size
        return True

    def find_free_block(self, size, algorithm):
        candidates = []
        for i, block in enumerate(self.memory):
            if block['free'] and block['size'] >= size:
                candidates.append((i, block))

        if not candidates:
            return None

        if algorithm == "最先适应":
            return candidates[0][0]
        elif algorithm == "最佳适应":
            candidates.sort(key=lambda x: x[1]['size'])
            return candidates[0][0]
        elif algorithm == "最坏适应":
            candidates.sort(key=lambda x: -x[1]['size'])
            return candidates[0][0]

    def deallocate(self, pid):
        if pid not in self.allocations:
            return False

        for i, block in enumerate(self.memory):
            if block['pid'] == pid:
                self.memory[i]['free'] = True
                self.memory[i]['pid'] = None
                break

        # 合并相邻空闲块
        self.merge_free_blocks()
        del self.allocations[pid]
        return True

    def merge_free_blocks(self):
        merged = []
        for block in self.memory:
            if not merged:
                merged.append(block)
            else:
                last = merged[-1]
                if last['free'] and block['free'] and \
                        last['start'] + last['size'] == block['start']:
                    last['size'] += block['size']
                else:
                    merged.append(block)
        self.memory = merged

    def get_memory_status(self):
        return sorted(self.memory, key=lambda x: x['start'])