"""
考研英语真题词频统计 — 桌面版入口
使用 pywebview 将 Flask Web 应用包装为原生桌面窗口。
支持 PyInstaller 打包成独立 .exe。
"""

import sys
import os
import threading

# ── 路径处理：区分开发环境和 PyInstaller 打包环境 ──
if getattr(sys, 'frozen', False):
    # 打包后的 exe：文件都被解压到 sys._MEIPASS 临时目录
    BUNDLE_DIR = sys._MEIPASS
else:
    # 开发环境：脚本所在目录即项目根目录
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

# 设置 Flask 应用查找资源的路径
os.environ['EXAM_WORDS_DB_PATH'] = os.path.join(BUNDLE_DIR, 'data', 'exam_words.db')

# ── 导入 Flask 应用 ──
from webapp.app import app

# 在 frozen 模式下覆盖 Flask 的模板和静态文件目录
if getattr(sys, 'frozen', False):
    app.template_folder = os.path.join(BUNDLE_DIR, 'webapp', 'templates')
    app.static_folder = os.path.join(BUNDLE_DIR, 'webapp', 'static')


def start_flask():
    """在后台线程启动 Flask（关闭 debug 和 reloader）"""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def main():
    # 后台线程启动 Flask
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # 打开原生桌面窗口
    import webview
    webview.create_window(
        title='考研英语真题词频统计',
        url='http://127.0.0.1:5000',
        width=1280,
        height=800,
        min_size=(900, 600),
        text_select=True,  # 允许选中文字
    )
    webview.start()


if __name__ == '__main__':
    main()
