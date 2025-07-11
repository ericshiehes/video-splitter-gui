# 🎬 视频工具箱 v2（FFmpeg GUI）

新版功能：
- ✅ 视频分割（自定义开始/结束时间，自动命名）
- ✅ 视频等分（如2等分、3等分）
- ✅ 提取视频音频为 MP3 格式
- ✅ 拖拽支持
- ✅ 自动分析视频信息（时长、编码、大小）
- ✅ 界面优化，支持 Tab 标签页切换

---

## 🖥️ 使用方法

```bash
pip install -r requirements.txt
python video_splitter.py
```

---

## 📝 依赖库

- tkinter（标准库）
- tkinterdnd2

---
✅ 图标嵌入方式
你下载的图标请保存为 icon.ico，与 .py 文件放在同一目录中，程序会通过以下代码自动加载图标：

```python
root.iconbitmap("icon.ico")
```

## 🧩 打包 EXE（可选）

如需将程序打包为 .exe 并包含图标，请运行以下命令（需先安装 pyinstaller）：

```bash
pip install pyinstaller
pyinstaller -F -w -i icon.ico your_script.py
```
其中：
-F：生成单一 .exe 文件
-w：不显示命令行窗口（适合 GUI）
-i icon.ico：设置程序图标

MIT License © 2025
