#!/usr/bin/env python3
"""
乃木坂46博客图片爬虫 - GUI界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import os

# 导入爬虫模块
from scraper import N46Scraper
from database import Database
from config import ensure_dirs, OUTPUT1_DIR, OUTPUT2_DIR
import asyncio


class RedirectText:
    """重定向stdout到Text控件"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        if '\n' in string:
            self.text_widget.insert(tk.END, self.buffer)
            self.text_widget.see(tk.END)
            self.buffer = ""
        self.text_widget.update()
        
    def flush(self):
        if self.buffer:
            self.text_widget.insert(tk.END, self.buffer)
            self.text_widget.see(tk.END)
            self.buffer = ""


class N46BlogGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("乃木坂46博客图片爬虫 v1.3")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 爬虫实例
        self.scraper = None
        self.running = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置grid权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # ===== 标题 =====
        title_label = ttk.Label(
            main_frame, 
            text="乃木坂46博客图片爬虫", 
            font=('Microsoft YaHei', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # ===== 模式选择 =====
        mode_frame = ttk.LabelFrame(main_frame, text="选择模式", padding="10")
        mode_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        mode_frame.columnconfigure(1, weight=1)
        
        self.mode_var = tk.StringVar(value="full")
        
        ttk.Radiobutton(
            mode_frame, 
            text="模式1：总检索（爬取所有成员）", 
            variable=self.mode_var, 
            value="full",
            command=self.on_mode_change
        ).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        ttk.Radiobutton(
            mode_frame, 
            text="模式2：指定成员检索", 
            variable=self.mode_var, 
            value="member",
            command=self.on_mode_change
        ).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # ===== 参数设置 =====
        params_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
        params_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        params_frame.columnconfigure(1, weight=1)
        
        # 页数设置
        ttk.Label(params_frame, text="爬取页数:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.pages_var = tk.StringVar(value="1")
        self.pages_spinbox = ttk.Spinbox(
            params_frame, 
            from_=1, 
            to=100, 
            textvariable=self.pages_var,
            width=10
        )
        self.pages_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(params_frame, text="(模式1每页约30-40篇，模式2每页约10篇)").grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # 成员名设置（模式2）
        ttk.Label(params_frame, text="成员名字:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.member_var = tk.StringVar()
        self.member_entry = ttk.Entry(params_frame, textvariable=self.member_var, width=30)
        self.member_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.member_entry.config(state='disabled')
        
        # 成员示例
        ttk.Label(params_frame, text='示例: "池田 瑛紗", "小川 彩"').grid(row=1, column=2, sticky=tk.W, padx=5)
        
        # ===== 操作按钮 =====
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.start_btn = ttk.Button(
            button_frame, 
            text="▶ 开始爬取", 
            command=self.start_crawl,
            width=15
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame, 
            text="⏹ 停止", 
            command=self.stop_crawl,
            width=15,
            state='disabled'
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="📊 查看统计", 
            command=self.show_stats,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="📁 打开输出目录", 
            command=self.open_output_dir,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # ===== 进度条 =====
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            variable=self.progress_var, 
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            font=('Microsoft YaHei', 9)
        )
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # ===== 日志输出 =====
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=20,
            font=('Consolas', 10)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 重定向stdout
        self.redirect = RedirectText(self.log_text)
        sys.stdout = self.redirect
        
        # ===== 说明文字 =====
        help_text = """使用说明:
• 模式1（总检索）：爬取乃木坂46官网所有成员的最新博客
• 模式2（成员检索）：针对特定成员的个人博客页面进行爬取
• 图片将自动按成员、日期、博客ID三种方式分类存储
• 首次运行会自动下载ChromeDriver，请耐心等待"""
        
        help_label = ttk.Label(
            main_frame, 
            text=help_text,
            justify=tk.LEFT,
            foreground='gray'
        )
        help_label.grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=10)
        
    def on_mode_change(self):
        """模式切换时更新UI"""
        mode = self.mode_var.get()
        if mode == "member":
            self.member_entry.config(state='normal')
            self.pages_var.set("3")
        else:
            self.member_entry.config(state='disabled')
            self.pages_var.set("1")
            
    def start_crawl(self):
        """开始爬取"""
        if self.running:
            return
            
        mode = self.mode_var.get()
        pages = self.pages_var.get()
        
        try:
            pages = int(pages)
            if pages < 1:
                raise ValueError("页数必须大于0")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的页数")
            return
            
        if mode == "member":
            member_name = self.member_var.get().strip()
            if not member_name:
                messagebox.showerror("错误", "请输入成员名字")
                return
                
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 更新UI状态
        self.running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress_var.set(0)
        
        # 在新线程中运行爬虫
        thread = threading.Thread(target=self.run_crawl, args=(mode, pages))
        thread.daemon = True
        thread.start()
        
    def run_crawl(self, mode, pages):
        """运行爬虫"""
        try:
            if mode == "full":
                self.status_var.set("模式1：正在爬取所有成员的博客...")
                self.run_full_mode(pages)
            else:
                member_name = self.member_var.get().strip()
                self.status_var.set(f"模式2：正在爬取成员 {member_name} 的博客...")
                self.run_member_mode(member_name, pages)
                
        except Exception as e:
            print(f"\n错误: {e}")
            messagebox.showerror("错误", str(e))
        finally:
            self.running = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.status_var.set("爬取完成")
            self.progress_var.set(100)
            
    def run_full_mode(self, pages):
        """运行模式1"""
        print(f"【模式1】总检索 - 爬取 {pages} 页")
        print("="*60)
        
        # 确保输出目录存在
        ensure_dirs()
        
        try:
            with N46Scraper() as scraper:
                # 爬取博客
                print("\n>>> 第一步：爬取博客列表")
                total = scraper.crawl_blog_list(start_page=1, max_pages=pages)
                
                # 下载图片
                print("\n>>> 第二步：下载图片")
                asyncio.run(scraper.download_images())
                
            print("\n全部完成！")
            messagebox.showinfo("完成", "爬取和下载已完成！")
            
        except Exception as e:
            print(f"\n运行出错: {e}")
            raise
            
    def run_member_mode(self, member_name, pages):
        """运行模式2"""
        print(f"【模式2】指定成员检索 - 成员: {member_name}, 页数: {pages}")
        print("="*60)
        
        # 确保输出目录存在
        ensure_dirs()
        
        try:
            with N46Scraper() as scraper:
                # 爬取指定成员
                total = scraper.crawl_by_member(member_name, max_pages=pages)
                
                if total > 0:
                    # 下载图片 - 使用mode2专用方法，按成员分类到output2
                    print("\n>>> 开始下载图片（按成员分类）")
                    asyncio.run(scraper.download_images_by_member(member_name))
                    print("\n全部完成！")
                    messagebox.showinfo("完成", f"成员 {member_name} 的爬取和下载已完成！\n图片保存在 output2/{member_name}/ 目录")
                else:
                    messagebox.showwarning("警告", "未找到该成员的博客")
                    
        except Exception as e:
            print(f"\n运行出错: {e}")
            raise
            
    def stop_crawl(self):
        """停止爬取"""
        if messagebox.askyesno("确认", "确定要停止爬取吗？"):
            self.running = False
            self.status_var.set("已停止")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            print("\n用户手动停止")
            
    def show_stats(self):
        """显示统计信息"""
        try:
            db = Database()
            stats = db.get_stats()
            
            stats_text = f"""
📊 数据库统计
{'='*40}
博客总数: {stats['total_blogs']}
图片总数: {stats['total_images']}
已下载: {stats['downloaded_images']}
待下载: {stats['pending_images']}
成员数: {stats['unique_members']}
{'='*40}
"""
            print(stats_text)
            messagebox.showinfo("统计信息", stats_text)
            
        except Exception as e:
            messagebox.showerror("错误", f"无法获取统计信息: {e}")
            
    def open_output_dir(self):
        """打开输出目录"""
        # 根据当前选择的模式决定打开哪个目录
        mode = self.mode_var.get()

        if mode == "member":
            # Mode2: 打开output2目录
            target_dir = OUTPUT2_DIR
            dir_name = "output2"
        else:
            # Mode1: 打开output1目录
            target_dir = OUTPUT1_DIR
            dir_name = "output1"

        if os.path.exists(target_dir):
            os.startfile(target_dir)
        else:
            # 目录不存在时创建并打开
            ensure_dirs()
            if os.path.exists(target_dir):
                os.startfile(target_dir)
            else:
                messagebox.showinfo("提示", f"{dir_name}目录创建失败")


def main():
    root = tk.Tk()
    app = N46BlogGUI(root)
    
    # 设置窗口关闭处理
    def on_closing():
        if app.running:
            if messagebox.askyesno("确认", "爬取正在进行中，确定要退出吗？"):
                root.destroy()
        else:
            root.destroy()
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
