from typing import Optional
from models.page_table import PageTable, PageTableEntry

class PageReplacementStrategy:
    def __init__(self, page_table: PageTable):
        self.page_table = page_table
    
    def handle_page_fault(self, page_number: int) -> int:
        """处理缺页中断，返回新页面的内存块号"""
        raise NotImplementedError

class FIFOStrategy(PageReplacementStrategy):
    def handle_page_fault(self, page_number: int) -> int:
        # 检查是否有空闲内存块
        used_frames = self.page_table.get_used_frames()
        
        if len(used_frames) < self.page_table.job_frames:
            # 有空闲块
            new_frame = len(used_frames)
        else:
            # 使用FIFO算法选择要淘汰的页面
            oldest_page = self.page_table.get_oldest_page()
            if oldest_page is None:
                raise ValueError("无法找到要淘汰的页面")
            
            # 如果页面被修改过，需要写回磁盘
            if oldest_page.modified:
                self.page_table.result_text.insert(tk.END, 
                    f"页面 {oldest_page.page_number} 被修改，需要写回磁盘\n")
            
            new_frame = oldest_page.frame_number
            self.page_table.remove_page(oldest_page.page_number)
        
        # 调入新页面
        self.page_table.update_page(page_number, new_frame)
        return new_frame 