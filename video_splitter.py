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

# 启动提示
def show_path_warning():
    if not CONFIG.get("suppress_path_warning", False):
        popup = tk.Toplevel()
        popup.title("提示")
        popup.geometry("360x120+500+300")
        popup.attributes("-topmost", True)
        tk.Label(popup, text="请确保 ffmpeg/bin 已加入系统 Path!").pack(pady=10)
        var = tk.BooleanVar()
        tk.Checkbutton(popup, text="不再显示", variable=var).pack()
        def on_ok():
            if var.get():
                CONFIG["suppress_path_warning"] = True
                save_config()
            popup.destroy()
        tk.Button(popup, text="确定", command=on_ok).pack(pady=5)
        popup.grab_set()

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

# 音频提取
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
    root.geometry("700x420")
    load_config()
    show_path_warning()

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # ---------- tab1 视频分割 ----------
    tab1 = ttk.Frame(notebook)
    input_path1, output_path1, info1 = tk.StringVar(), tk.StringVar(), tk.StringVar()
    start_time, end_time = [tk.StringVar(value="00:00:00") for _ in range(2)]

    def choose_file1():
        path = filedialog.askopenfilename()
        if path:
            input_path1.set(path)
            dur, codec, _ = get_video_info(path)
            info1.set(f"{codec} | 时长: {dur}")
            name, ext = os.path.splitext(os.path.basename(path))
            output_path1.set(os.path.join(os.path.dirname(path), f"{name}_1{ext}"))

    def choose_output1():
        path = filedialog.asksaveasfilename(defaultextension=".mp4")
        if path:
            output_path1.set(path)

    def run_split():
        split_video(input_path1.get(), start_time.get(), end_time.get(), output_path1.get(),
                    lambda ok: messagebox.showinfo("成功" if ok else "失败", "分割完成" if ok else "分割失败"))

    ttk.Label(tab1, text="选择文件：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab1, textvariable=input_path1, width=60).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(tab1, text="浏览", command=choose_file1).grid(row=0, column=2, padx=5, pady=5)
    tab1.drop_target_register(DND_FILES)
    tab1.dnd_bind('<<Drop>>', lambda e: (input_path1.set(e.data), choose_file1()))

    tk.Label(tab1, textvariable=info1).grid(row=1, column=0, columnspan=3, padx=5)

    ttk.Label(tab1, text="开始时间：").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab1, textvariable=start_time, width=10).grid(row=2, column=1, sticky="w")
    ttk.Label(tab1, text="结束时间：").grid(row=2, column=1, padx=90, pady=5, sticky="w")
    tk.Entry(tab1, textvariable=end_time, width=10).grid(row=2, column=1, padx=180, sticky="w")

    ttk.Label(tab1, text="输出路径：").grid(row=3, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab1, textvariable=output_path1, width=60).grid(row=3, column=1, padx=5, pady=5)
    tk.Button(tab1, text="选择", command=choose_output1).grid(row=3, column=2, padx=5, pady=5)

    tk.Button(tab1, text="分割", command=run_split).grid(row=4, column=1, pady=10)
    notebook.add(tab1, text="视频分割")

    # ---------- tab2 等分 ----------
    tab2 = ttk.Frame(notebook)
    input_path2, info2, part_num = tk.StringVar(), tk.StringVar(), tk.IntVar(value=2)

    def choose_file2():
        path = filedialog.askopenfilename()
        if path:
            input_path2.set(path)
            dur, codec, size = get_video_info(path)
            info2.set(f"{codec} | 时长: {dur} | 大小: {size}")

    def run_equal():
        name, _ = os.path.splitext(input_path2.get())
        split_equally(input_path2.get(), part_num.get(), name,
                      lambda ok: messagebox.showinfo("成功" if ok else "失败", "分割完成" if ok else "分割失败"))

    ttk.Label(tab2, text="选择文件：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab2, textvariable=input_path2, width=60).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(tab2, text="浏览", command=choose_file2).grid(row=0, column=2, padx=5, pady=5)
    tab2.drop_target_register(DND_FILES)
    tab2.dnd_bind('<<Drop>>', lambda e: (input_path2.set(e.data), choose_file2()))

    tk.Label(tab2, textvariable=info2).grid(row=1, column=0, columnspan=3, padx=5)

    tk.Label(tab2, text="等分为：").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab2, textvariable=part_num, width=5).grid(row=2, column=1, sticky="w")
    tk.Button(tab2, text="确定分割", command=run_equal).grid(row=3, column=1, pady=10)
    notebook.add(tab2, text="视频等分")

    # ---------- tab3 提取音频 ----------
    tab3 = ttk.Frame(notebook)
    input_path3 = tk.StringVar()

    def choose_file3():
        path = filedialog.askopenfilename()
        if path:
            input_path3.set(path)

    def run_audio():
        name, _ = os.path.splitext(input_path3.get())
        extract_audio(input_path3.get(), name + ".mp3",
                      lambda ok: messagebox.showinfo("成功" if ok else "失败", "提取成功" if ok else "失败"))

    ttk.Label(tab3, text="选择文件：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(tab3, textvariable=input_path3, width=60).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(tab3, text="浏览", command=choose_file3).grid(row=0, column=2, padx=5, pady=5)
    tab3.drop_target_register(DND_FILES)
    tab3.dnd_bind('<<Drop>>', lambda e: (input_path3.set(e.data), choose_file3()))

    tk.Button(tab3, text="提取 MP3", command=run_audio).grid(row=1, column=1, pady=10)
    notebook.add(tab3, text="提取音频")

    root.mainloop()

if __name__ == "__main__":
    build_gui()
