import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess
import os
import json
import threading

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def show_path_warning():
    config = load_config()
    if not config.get("suppress_path_warning", False):
        def on_ok():
            if var.get():
                config["suppress_path_warning"] = True
                save_config(config)
            popup.destroy()

        popup = tk.Toplevel()
        popup.title("提示")
        tk.Label(popup, text="请确保 ffmpeg 的 bin 目录已加入系统 Path 环境变量！").pack(pady=10)
        var = tk.BooleanVar()
        tk.Checkbutton(popup, text="不再显示此提示", variable=var).pack()
        tk.Button(popup, text="确定", command=on_ok).pack(pady=10)
        popup.grab_set()

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("视频文件", "*.mp4;*.mov;*.mkv;*.avi")])
    if file_path:
        handle_file_select(file_path)

def handle_file_select(file_path):
    input_path.set(file_path)
    get_video_info(file_path)
    update_output_path(file_path)

def get_video_info(file_path):
    try:
        cmd = ["ffmpeg", "-i", file_path]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        output = result.stderr
        duration = ""
        codec = ""
        for line in output.splitlines():
            if "Duration" in line:
                duration = line.strip().split(",")[0].split("Duration:")[1].strip()
            if "Stream" in line and "Video" in line:
                codec = line.split(":")[2].split(",")[0].strip()
                break
        video_info.set(f"编码: {codec}   时长: {duration}")
    except Exception as e:
        messagebox.showerror("错误", f"获取视频信息失败：{e}")

def update_output_path(file_path):
    base = os.path.splitext(file_path)[0]
    folder = base + "_1"
    os.makedirs(folder, exist_ok=True)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    output_file = os.path.join(folder, f"{name}_split{ext}")
    output_path.set(output_file)

def run_ffmpeg():
    in_file = input_path.get()
    start_time = start_entry.get()
    end_time = end_entry.get()
    out_file = output_path.get()

    if not in_file or not start_time or not end_time or not out_file:
        messagebox.showwarning("警告", "所有字段都必须填写！")
        return

    progress_bar["value"] = 0
    progress_bar.update()

    def task():
        cmd = [
            "ffmpeg", "-y",
            "-i", in_file,
            "-ss", start_time,
            "-to", end_time,
            "-c", "copy", out_file
        ]
        try:
            # 模拟进度条（实际根据文件大小估计时间较困难）
            for i in range(1, 101):
                progress_bar["value"] = i
                progress_bar.update()
                root.after(20)

            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            progress_bar["value"] = 100
            messagebox.showinfo("完成", "视频分割完成！")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("错误", f"执行分割失败：{e}")
        finally:
            progress_bar["value"] = 0

    threading.Thread(target=task).start()

# 初始化窗口
root = TkinterDnD.Tk()
root.title("视频分割工具")
root.geometry("620x330")

show_path_warning()

# 变量
input_path = tk.StringVar()
video_info = tk.StringVar()
output_path = tk.StringVar()

# 文件选择
tk.Label(root, text="选择视频文件:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
entry = tk.Entry(root, textvariable=input_path, width=50)
entry.grid(row=0, column=1)
entry.drop_target_register(DND_FILES)
entry.dnd_bind('<<Drop>>', lambda e: handle_file_select(e.data.strip('{}')))
tk.Button(root, text="选择", command=select_file).grid(row=0, column=2, padx=5)

# 视频信息
tk.Label(root, textvariable=video_info).grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="w")

# 时间输入
tk.Label(root, text="开始时间(HH:MM:SS):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
start_entry = tk.Entry(root)
start_entry.grid(row=2, column=1, sticky="w")

tk.Label(root, text="结束时间(HH:MM:SS):").grid(row=3, column=0, padx=10, pady=5, sticky="e")
end_entry = tk.Entry(root)
end_entry.grid(row=3, column=1, sticky="w")

# 输出路径
tk.Label(root, text="输出文件路径:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
tk.Entry(root, textvariable=output_path, width=50).grid(row=4, column=1)
tk.Button(root, text="浏览", command=lambda: output_path.set(filedialog.asksaveasfilename())).grid(row=4, column=2, padx=5)

# 进度条
progress_bar = ttk.Progressbar(root, length=500, mode='determinate')
progress_bar.grid(row=5, column=0, columnspan=3, pady=10)

# 操作按钮
tk.Button(root, text="确定", command=run_ffmpeg).grid(row=6, column=1, sticky="e", pady=20)
tk.Button(root, text="退出", command=root.quit).grid(row=6, column=2, padx=5, pady=20)

root.mainloop()
