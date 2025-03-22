import time
from typing import List, Optional

class PageTableEntry:
    def __init__(self, page_number: int, present: bool, frame_number: int, 
                 modified: bool, disk_location: str):
        self.page_number = page_number
        self.present = present
        self.frame_number = frame_number
        self.modified = modified
        self.disk_location = disk_location
        self.load_time = time.time()  # 用于FIFO算法

class PageTable:
    def __init__(self, entries: List[PageTableEntry]):
        self.entries = entries
        self.memory_size = 64 * 1024  # 64KB
        self.block_size = 1024  # 1KB
        self.total_frames = self.memory_size // self.block_size
        self.job_frames = 2  # 作业分得的内存块数
    
    def get_entry(self, page_number: int) -> Optional[PageTableEntry]:
        if 0 <= page_number < len(self.entries):
            return self.entries[page_number]
        return None
    
    def is_page_in_memory(self, page_number: int) -> bool:
        entry = self.get_entry(page_number)
        return entry is not None and entry.present
    
    def get_physical_address(self, page_number: int, offset: int) -> int:
        entry = self.get_entry(page_number)
        if entry is None or not entry.present:
            raise ValueError(f"页面 {page_number} 不在内存中")
        return entry.frame_number * self.block_size + offset
    
    def update_page(self, page_number: int, frame_number: int, modified: bool = False):
        entry = self.get_entry(page_number)
        if entry is not None:
            entry.present = True
            entry.frame_number = frame_number
            entry.modified = modified
            entry.load_time = time.time()
    
    def remove_page(self, page_number: int):
        entry = self.get_entry(page_number)
        if entry is not None:
            entry.present = False
            entry.frame_number = -1
    
    def get_used_frames(self) -> List[int]:
        return [entry.frame_number for entry in self.entries 
                if entry.present and entry.frame_number < self.job_frames]
    
    def get_oldest_page(self) -> Optional[PageTableEntry]:
        present_pages = [entry for entry in self.entries[:self.job_frames] if entry.present]
        if not present_pages:
            return None
        return min(present_pages, key=lambda x: x.load_time) 