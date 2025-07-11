import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess
import os
import threading
import json

CONFIG = {"suppress_path_warning": False}
CONFIG_FILE = "config.json"

# 加载配置
def load_config():
    global CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                CONFIG = json.load(f)
        except:
            CONFIG = {"suppress_path_warning": False}

# 保存配置
def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(CONFIG, f)

# 居中窗口
def center_window(window, width=600, height=300):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

# 启动提示
def show_path_warning(root):
    if not CONFIG.get("suppress_path_warning", False):
        popup = tk.Toplevel(root)
        popup.title("提示")
        popup.attributes("-topmost", True)
        center_window(popup, 360, 120)
        tk.Label(popup, text="请确保 ffmpeg/bin 已加入系统 Path!").pack(pady=10)
        var = tk.BooleanVar()
        tk.Checkbutton(popup, text="不再显示", variable=var).pack()
        def on_ok():
            if var.get():
                CONFIG["suppress_path_warning"] = True
                save_config()
            popup.destroy()
            root.deiconify()
        tk.Button(popup, text="确定", command=on_ok).pack(pady=5)
        popup.grab_set()
        root.withdraw()

# 解析视频信息
def get_video_info(filepath):
    try:
        result = subprocess.run(["ffmpeg", "-i", filepath], stderr=subprocess.PIPE, text=True)
        lines = result.stderr.splitlines()
        duration, codec, size = "", "", os.path.getsize(filepath) / 1024 / 1024
        for line in lines:
            if "Duration" in line:
                duration = line.split("Duration:")[1].split(",")[0].strip()
            if "Stream" in line and "Video" in line:
                codec = line.split(":")[-1].split(",")[0].strip()
                break
        return duration, codec, f"{size:.2f} MB"
    except:
        return "", "", ""

# 分割功能
def split_video(input_file, start, end, output_file, callback):
    def task():
        try:
            subprocess.run(["ffmpeg", "-y", "-i", input_file, "-ss", start, "-to", end, "-c", "copy", output_file],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            callback(True)
        except:
            callback(False)
    threading.Thread(target=task).start()

# 等分功能
def split_equally(input_file, parts, output_prefix, callback):
    def task():
        try:
            result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                     "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_file],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            total_duration = float(result.stdout.strip())
            each = total_duration / parts
            for i in range(parts):
                ss = str(int(each * i))
                to = str(int(each * (i + 1)))
                out = f"{output_prefix}_{i + 1}.mp4"
                subprocess.run(["ffmpeg", "-y", "-i", input_file, "-ss", ss, "-to", to, "-c", "copy", out],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            callback(True)
        except:
            callback(False)
    threading.Thread(target=task).start()

# 提取音频
def extract_audio(input_file, output_file, callback):
    def task():
        try:
            subprocess.run(["ffmpeg", "-y", "-i", input_file, "-q:a", "0", "-map", "a", output_file],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            callback(True)
        except:
            callback(False)
    threading.Thread(target=task).start()

# 构建 UI
def build_gui():
    root = TkinterDnD.Tk()
    root.title("FFmpeg 视频工具箱")
    center_window(root, 600, 300)
    root.iconbitmap("icon.ico")  # 设置程序图标，请将图标文件命名为 icon.ico 并放在同一目录
    load_config()
    show_path_warning(root)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # ---------- tab1 视频分割 ----------
    tab1 = ttk.Frame(notebook)
    tab1.grid_columnconfigure(1, weight=1)
    input_path1, output_path1, info1 = tk.StringVar(), tk.StringVar(), tk.StringVar()
    start_time, end_time = [tk.StringVar(value="00:00:00") for _ in range(2)]

    def set_input1(path):
        if path:
            input_path1.set(path)
            dur, codec, _ = get_video_info(path)
            info1.set(f"{codec} | 时长: {dur}")
            name, ext = os.path.splitext(os.path.basename(path))
            output_path1.set(os.path.join(os.path.dirname(path), f"{name}_1{ext}"))

    def choose_file1():
        path = filedialog.askopenfilename()
        set_input1(path)

    def choose_output1():
        folder = filedialog.askdirectory()
        if folder and input_path1.get():
            name, ext = os.path.splitext(os.path.basename(input_path1.get()))
            output_path1.set(os.path.join(folder, f"{name}_1{ext}"))

    def run_split():
        split_video(input_path1.get(), start_time.get(), end_time.get(), output_path1.get(),
                    lambda ok: messagebox.showinfo("成功" if ok else "失败", "分割完成" if ok else "分割失败"))

    ttk.Label(tab1, text="选择文件：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab1, textvariable=input_path1).grid(row=0, column=1, padx=5, pady=5, sticky="we")
    tk.Button(tab1, text="浏览", command=choose_file1).grid(row=0, column=2, padx=5, pady=5)
    tab1.drop_target_register(DND_FILES)
    tab1.dnd_bind('<<Drop>>', lambda e: set_input1(e.data.strip('{}')))

    tk.Label(tab1, textvariable=info1).grid(row=1, column=0, columnspan=3, padx=5, sticky="w")

    ttk.Label(tab1, text="时间范围：").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    frame_time = ttk.Frame(tab1)
    frame_time.grid(row=2, column=1, columnspan=2, sticky="w")
    tk.Entry(frame_time, textvariable=start_time, width=10).pack(side="left")
    ttk.Label(frame_time, text="至").pack(side="left", padx=5)
    tk.Entry(frame_time, textvariable=end_time, width=10).pack(side="left")

    ttk.Label(tab1, text="输出路径：").grid(row=3, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab1, textvariable=output_path1).grid(row=3, column=1, padx=5, pady=5, sticky="we")
    tk.Button(tab1, text="选择", command=choose_output1).grid(row=3, column=2, padx=5, pady=5)

    tk.Button(tab1, text="分割", command=run_split).grid(row=4, column=1, pady=10)
    notebook.add(tab1, text="视频分割")

    # ---------- tab2 视频等分 ----------
    tab2 = ttk.Frame(notebook)
    tab2.grid_columnconfigure(1, weight=1)
    input_path2, info2, parts = tk.StringVar(), tk.StringVar(), tk.IntVar(value=2)

    def set_input2(path):
        if path:
            input_path2.set(path)
            dur, codec, size = get_video_info(path)
            info2.set(f"{codec} | 时长: {dur} | 大小: {size}")

    def choose_file2():
        path = filedialog.askopenfilename()
        set_input2(path)

    def run_split_eq():
        if input_path2.get():
            name, _ = os.path.splitext(os.path.basename(input_path2.get()))
            folder = os.path.dirname(input_path2.get())
            split_equally(input_path2.get(), parts.get(), os.path.join(folder, name),
                          lambda ok: messagebox.showinfo("成功" if ok else "失败", "已完成" if ok else "失败"))

    ttk.Label(tab2, text="选择文件：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab2, textvariable=input_path2).grid(row=0, column=1, padx=5, pady=5, sticky="we")
    tk.Button(tab2, text="浏览", command=choose_file2).grid(row=0, column=2, padx=5, pady=5)
    tab2.drop_target_register(DND_FILES)
    tab2.dnd_bind('<<Drop>>', lambda e: set_input2(e.data.strip('{}')))

    tk.Label(tab2, textvariable=info2).grid(row=1, column=0, columnspan=3, padx=5, sticky="w")
    ttk.Label(tab2, text="等分数量：").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    tk.Spinbox(tab2, from_=2, to=20, textvariable=parts).grid(row=2, column=1, padx=5, pady=5, sticky="w")
    tk.Button(tab2, text="开始分割", command=run_split_eq).grid(row=3, column=1, pady=10)
    notebook.add(tab2, text="视频等分")

    # ---------- tab3 提取音频 ----------
    tab3 = ttk.Frame(notebook)
    tab3.grid_columnconfigure(1, weight=1)
    input_path3 = tk.StringVar()

    def set_input3(path):
        if path:
            input_path3.set(path)

    def choose_file3():
        path = filedialog.askopenfilename()
        set_input3(path)

    def run_extract():
        if input_path3.get():
            name = os.path.splitext(os.path.basename(input_path3.get()))[0]
            folder = os.path.dirname(input_path3.get())
            output_mp3 = os.path.join(folder, f"{name}.mp3")
            extract_audio(input_path3.get(), output_mp3,
                          lambda ok: messagebox.showinfo("成功" if ok else "失败", "已完成" if ok else "失败"))

    ttk.Label(tab3, text="选择文件：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab3, textvariable=input_path3).grid(row=0, column=1, padx=5, pady=5, sticky="we")
    tk.Button(tab3, text="浏览", command=choose_file3).grid(row=0, column=2, padx=5, pady=5)
    tab3.drop_target_register(DND_FILES)
    tab3.dnd_bind('<<Drop>>', lambda e: set_input3(e.data.strip('{}')))
    tk.Button(tab3, text="提取音频", command=run_extract).grid(row=1, column=1, pady=10)
    notebook.add(tab3, text="提取音频")

    root.mainloop()

if __name__ == "__main__":
    build_gui()
