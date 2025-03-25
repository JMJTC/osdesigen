import tkinter as tk
from tkinter import ttk, messagebox


class MemorySimulation:
    def __init__(self, root):
        # 初始化函数，设置根窗口，内存管理器，整体样式，创建小部件，更新显示，设置快捷键
        self.handle_deallocate = None
        self.handle_allocate = None
        self.show_hover_info = None
        self.set_total_memory = None
        self.handle_redo = None
        self.handle_undo = None
        self.root = root
        # self.memory = MemoryManager(1024)
        self.root.configure(bg='#f0f0f0')
        self.create_widgets()
        # self.update_display()
        # self.setup_shortcuts()

    def create_widgets(self):
        # 设置整体样式
        # 创建一个样式对象
        style = ttk.Style()
        # 配置Treeview的背景色、字段背景色和前景色
        style.configure('Treeview', background='white', fieldbackground='white', foreground='black')
        # 配置Treeview的标题背景色和前景色
        style.configure('Treeview.Heading', background='#e1e1e1', foreground='black')
        # 配置TLabelframe的背景色
        style.configure('TLabelframe', background='#f0f0f0')
        # 配置TLabelframe的标签背景色和字体
        style.configure('TLabelframe.Label', background='#f0f0f0', font=('微软雅黑', 10))
        # 配置TButton的填充
        style.configure('TButton', padding=5)
        # 配置TEntry的填充
        style.configure('TEntry', padding=5)

        # 添加工具栏
        # 创建一个Frame对象，作为工具栏
        toolbar = tk.Frame(self.root, bg='#f0f0f0')
        # 将工具栏放置在窗口的顶部，并填充水平方向
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Button(toolbar, text="撤销 (Ctrl+Z)", command=self.handle_undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="重做 (Ctrl+Y)", command=self.handle_redo).pack(side=tk.LEFT, padx=2)

        # 添加内存大小设置
        # 在工具栏中添加一个标签，显示“总内存大小：”
        ttk.Label(toolbar, text="总内存大小:").pack(side=tk.LEFT, padx=5)
        # 创建一个字符串变量，用于存储总内存大小
        self.total_memory_var = tk.StringVar(value="1024")
        # 在工具栏中添加一个输入框，用于输入总内存大小
        self.total_memory_entry = ttk.Entry(toolbar, textvariable=self.total_memory_var, width=10)
        self.total_memory_entry.pack(side=tk.LEFT, padx=2)
        # 在工具栏中添加一个按钮，点击按钮时调用set_total_memory方法
        ttk.Button(toolbar, text="设置", command=self.set_total_memory).pack(side=tk.LEFT, padx=2)

        # 左侧面板
        # 创建一个Frame，作为左侧的框架
        left_frame = tk.Frame(self.root, bg='#f0f0f0')
        # 将框架放置在窗口的左侧，并填充整个窗口，同时设置左右和上下的内边距为10
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 内存可视化区域
        # 创建一个Frame，用于放置画布
        canvas_frame = tk.Frame(left_frame, bg='#f0f0f0')
        # 将Frame放置在left_frame中，填充水平方向，上下边距为0和10
        canvas_frame.pack(fill=tk.X, pady=(0, 10))

        # 创建一个Canvas对象，用于显示图像
        self.canvas = tk.Canvas(canvas_frame, height=120, bg='white', highlightthickness=1,
                                highlightbackground='#cccccc')
        # 将Canvas对象放置在canvas_frame中，并填充水平方向
        self.canvas.pack(fill=tk.X)
        # 绑定鼠标移动事件，当鼠标移动时，调用show_hover_info方法
        self.canvas.bind('<Motion>', self.show_hover_info)

        # 分区表
        # 创建一个Frame，作为左侧框架的子组件
        table_frame = tk.Frame(left_frame, bg='#f0f0f0')
        # 将Frame填充到左侧框架中，并设置可扩展
        table_frame.pack(fill=tk.BOTH, expand=True)

        # 空闲分区表
        # 创建一个标签，显示可用分区表
        free_label = tk.Label(table_frame, text="可用分区表", bg='#f0f0f0', font=('微软雅黑', 10, 'bold'))
        # 将标签放置在table_frame中，并设置垂直方向上的内边距
        free_label.pack(pady=(0, 5))
        # 创建一个Treeview控件，用于显示可用分区表
        self.free_table = ttk.Treeview(table_frame, columns=('start', 'size'), show='headings', height=5)
        # 设置Treeview控件的列标题
        self.free_table.heading('start', text='起始地址')
        self.free_table.heading('size', text='大小')
        # 将Treeview控件放置在table_frame中，并设置水平方向上的填充和垂直方向上的内边距
        self.free_table.pack(fill=tk.X, pady=(0, 10))

        # 已分配分区表
        # 创建一个标签，显示已分配分区表
        alloc_label = tk.Label(table_frame, text="已分配分区表", bg='#f0f0f0', font=('微软雅黑', 10, 'bold'))
        # 将标签放置在table_frame中，并设置上下边距为5
        alloc_label.pack(pady=(0, 5))
        # 创建一个Treeview控件，用于显示已分配分区表
        self.alloc_table = ttk.Treeview(table_frame, columns=('pid', 'start', 'size'), show='headings', height=5)
        # 设置Treeview控件的列标题
        self.alloc_table.heading('pid', text='进程ID')
        self.alloc_table.heading('start', text='起始地址')
        self.alloc_table.heading('size', text='大小')
        # 将Treeview控件放置在table_frame中，并填充水平方向
        self.alloc_table.pack(fill=tk.X)

        # 右侧面板
        # 创建一个Frame，作为右侧的框架
        right_frame = tk.Frame(self.root, bg='#f0f0f0')
        # 将框架放置在右侧，填充纵向空间，左右填充10像素，上下填充10像素
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # 算法选择
        # 创建一个标签框架，用于存放分配算法的选项
        algo_frame = ttk.LabelFrame(right_frame, text="分配算法", padding=10)
        # 将标签框架放置在右侧框架中，并设置垂直间距
        algo_frame.pack(pady=(0, 10))
        # 创建一个字符串变量，用于存储选择的分配算法
        self.algo_var = tk.StringVar(value='first_fit')
        # 定义分配算法的选项
        algorithms = [('最先适应', 'first_fit'),
                      ('最佳适应', 'best_fit'),
                      ('最坏适应', 'worst_fit')]
        # 遍历分配算法的选项
        for text, value in algorithms:
            # 创建一个单选按钮，用于选择分配算法
            rb = ttk.Radiobutton(algo_frame, text=text, variable=self.algo_var,
                                 value=value)
            # 将单选按钮放置在标签框架中，并设置水平对齐方式和垂直间距
            rb.pack(anchor=tk.W, pady=2)

        # 分配操作
        # 创建一个标签框架，用于分配内存
        alloc_frame = ttk.LabelFrame(right_frame, text="分配内存", padding=10)
        # 将标签框架放置在右侧框架中，并设置垂直间距
        alloc_frame.pack(pady=(0, 10))
        # 在标签框架中添加一个标签，用于提示用户输入大小
        ttk.Label(alloc_frame, text="大小:").pack(anchor=tk.W)
        # 创建一个文本框，用于用户输入大小
        self.size_entry = ttk.Entry(alloc_frame)
        # 将文本框放置在标签框架中，并设置填充方式和垂直间距
        self.size_entry.pack(fill=tk.X, pady=(0, 5))
        # 创建一个按钮，用于触发分配内存的操作
        ttk.Button(alloc_frame, text="分配", command=self.handle_allocate).pack(fill=tk.X)
        # 释放操作
        # 创建一个LabelFrame，用于显示释放内存的选项
        free_frame = ttk.LabelFrame(right_frame, text="释放内存", padding=10)
        # 将LabelFrame放置在右侧框架中，并设置垂直间距
        free_frame.pack(pady=(0, 10))
        # 在LabelFrame中添加一个标签，用于显示进程ID
        ttk.Label(free_frame, text="进程ID:").pack(anchor=tk.W)
        # 创建一个Entry，用于输入进程ID
        self.pid_entry = ttk.Entry(free_frame)
        # 将Entry放置在LabelFrame中，并设置水平填充和垂直间距
        self.pid_entry.pack(fill=tk.X, pady=(0, 5))
        # 创建一个Button，用于触发释放内存的操作
        ttk.Button(free_frame, text="释放", command=self.handle_deallocate).pack(fill=tk.X)

        # 信息显示
        # 创建一个LabelFrame，用于显示操作日志
        info_frame = ttk.LabelFrame(right_frame, text="操作日志", padding=10)
        # 将LabelFrame放置在右侧框架中，并填充整个框架
        info_frame.pack(fill=tk.BOTH, expand=True)
        # 创建一个Text控件，用于显示操作日志
        self.info_text = tk.Text(info_frame, height=10, width=30, bg='white',
                                 font=('Consolas', 9), padx=5, pady=5)
        # 将Text控件放置在LabelFrame中，并填充整个LabelFrame
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # 添加状态栏
        # 创建一个Frame，用于显示内存使用率和碎片率
        # 创建一个Frame，用于显示状态信息
        status_frame = tk.Frame(left_frame, bg='#f0f0f0')
        # 将Frame放置在left_frame的底部，并填充水平空间，设置内边距
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # 创建一个Label，用于显示内存使用率
        # 创建一个标签，用于显示内存使用率
        self.usage_label = tk.Label(status_frame, text="内存使用率: 0%", bg='#f0f0f0', font=('微软雅黑', 9))
        # 将标签放置在status_frame中，并填充整个区域，左右各留出5个像素的间距
        self.usage_label.pack(fill=tk.BOTH, padx=5)

        # 创建一个Label，用于显示碎片率
        self.frag_label = tk.Label(status_frame, text="碎片率: 0%", bg='#f0f0f0', font=('微软雅黑', 9))
        self.frag_label.pack(fill=tk.BOTH, padx=5)
