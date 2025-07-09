# 🎬 视频分割工具（FFmpeg GUI）

一个基于 Python + tkinter 的 Windows 视频分割工具，支持：
- 拖拽视频文件
- 设置分割时间
- 自动生成输出路径
- 显示视频编码与时长信息
- 一键执行分割
- 简洁易用、纯绿色程序

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## ▶️ 运行程序

```bash
python video_splitter.py
```

## 📦 打包为 .exe

```bash
pip install pyinstaller
pyinstaller -F -w video_splitter.py
```

MIT License © 2025
