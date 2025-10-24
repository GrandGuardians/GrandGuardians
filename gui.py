"""简单的可视化界面：

- 使用 Tkinter 实现一个小型 GUI，支持加密和解密文本或文件。
- 动态加载同目录下的 `1.py`（由于模块名为数字，使用 importlib 根据文件路径加载）。

功能：
- 密码输入框
- 文本输入（可粘贴中文/英文）
- Token 输出（base64）
- 加密 / 解密 按钮
- 从文件加载文本、将输出保存到文件
- 复制输出到剪贴板、状态提示

用法：直接运行此文件：
    python gui.py

"""

from __future__ import annotations

import importlib.util
import os
import sys
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox

HERE = os.path.dirname(__file__) if __file__ else os.getcwd()
MODULE_PATH = os.path.join(HERE, "1.py")
SETTINGS_PATH = os.path.join(HERE, ".gui_settings.json")

import json


class Settings:
    """简单的 JSON 设置管理：记住密码与最近文件列表。"""
    def __init__(self, path: str = SETTINGS_PATH):
        self.path = path
        self.remember_password = False
        self.password = ""
        self.recent_files: list[str] = []
        self._max_recent = 8
        self.load()

    def load(self) -> None:
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.remember_password = bool(data.get('remember_password', False))
                self.password = str(data.get('password', '')) if self.remember_password else ''
                self.recent_files = list(dict.fromkeys(data.get('recent_files', [])))[: self._max_recent]
        except Exception:
            # 忽略读取错误，保持默认
            self.remember_password = False
            self.password = ''
            self.recent_files = []

    def save(self) -> None:
        try:
            data = {
                'remember_password': bool(self.remember_password),
                'password': self.password if self.remember_password else '',
                'recent_files': list(self.recent_files[: self._max_recent]),
            }
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            # 写失败不抛出
            pass

    def add_recent(self, filepath: str) -> None:
        try:
            if not filepath:
                return
            # 最近优先，去重
            if filepath in self.recent_files:
                self.recent_files.remove(filepath)
            self.recent_files.insert(0, filepath)
            self.recent_files = self.recent_files[: self._max_recent]
            self.save()
        except Exception:
            pass



def load_encrypt_module(path: str):
    """按路径动态加载模块并返回包含 encrypt/decrypt 的模块对象。"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到 {path}")
    spec = importlib.util.spec_from_file_location("encrypt_module", path)
    if spec is None or spec.loader is None:
        raise ImportError("无法创建模块规范")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    # 验证存在 encrypt/decrypt
    if not hasattr(mod, "encrypt") or not hasattr(mod, "decrypt"):
        raise AttributeError("模块中未找到 encrypt/decrypt 函数")
    return mod


class CryptoGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("加密/解密 工具")
        root.geometry("800x600")

        # 顶部：密码、记住密码与最近文件
        self.settings = Settings()

        frm_top = tk.Frame(root)
        frm_top.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(frm_top, text="密码:").pack(side=tk.LEFT)
        self.entry_password = tk.Entry(frm_top, show="*", width=32)
        self.entry_password.pack(side=tk.LEFT, padx=6)
        # 记住密码复选
        self.var_remember = tk.BooleanVar(value=self.settings.remember_password)
        chk = tk.Checkbutton(frm_top, text="记住密码", variable=self.var_remember, command=self._on_toggle_remember)
        chk.pack(side=tk.LEFT)
        # 最近文件下拉
        tk.Label(frm_top, text="最近文件:").pack(side=tk.LEFT, padx=8)
        # 修复 OptionMenu 参数错误：至少要有一个选项（必须在 __init__ 方法体内）
        recent_list = self.settings.recent_files if self.settings.recent_files else ['']
        self.var_recent = tk.StringVar(value=recent_list[0])
        self.opt_recent = tk.OptionMenu(frm_top, self.var_recent, *recent_list, command=self._on_select_recent)
        self.opt_recent.config(width=24)
        self.opt_recent.pack(side=tk.LEFT, padx=6)


        tk.Button(frm_top, text="加载加密模块", command=self._on_load_module).pack(side=tk.RIGHT)
        self.lbl_module = tk.Label(frm_top, text=os.path.basename(MODULE_PATH))
        self.lbl_module.pack(side=tk.RIGHT, padx=6)

        # 如果设置记住密码则填充
        if self.settings.remember_password and self.settings.password:
            try:
                self.entry_password.insert(0, self.settings.password)
            except Exception:
                pass

        # 中间：输入文本与输出 token
        frm_mid = tk.Frame(root)
        frm_mid.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        left = tk.Frame(frm_mid)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left, text="原文 / 待加密文本（支持中文）:").pack(anchor=tk.W)
        self.txt_input = tk.Text(left, wrap=tk.WORD)
        self.txt_input.pack(fill=tk.BOTH, expand=True)
        btn_row = tk.Frame(left)
        btn_row.pack(fill=tk.X)
        tk.Button(btn_row, text="从文件加载", command=self._load_from_file).pack(side=tk.LEFT)
        tk.Button(btn_row, text="清空", command=lambda: self.txt_input.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=6)

        right = tk.Frame(frm_mid)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(right, text="Token / 加密后文本 (base64):").pack(anchor=tk.W)
        self.txt_output = tk.Text(right, wrap=tk.WORD)
        self.txt_output.pack(fill=tk.BOTH, expand=True)
        btn_row2 = tk.Frame(right)
        btn_row2.pack(fill=tk.X)
        tk.Button(btn_row2, text="保存到文件", command=self._save_output_to_file).pack(side=tk.LEFT)
        tk.Button(btn_row2, text="复制到剪贴板", command=self._copy_output).pack(side=tk.LEFT, padx=6)

        # 底部：操作按钮和状态
        frm_bottom = tk.Frame(root)
        frm_bottom.pack(fill=tk.X, padx=8, pady=6)
        tk.Button(frm_bottom, text="加密", command=self._run_encrypt, width=12).pack(side=tk.LEFT)
        tk.Button(frm_bottom, text="解密", command=self._run_decrypt, width=12).pack(side=tk.LEFT, padx=8)
        tk.Button(frm_bottom, text="清空输出", command=lambda: self.txt_output.delete(1.0, tk.END)).pack(side=tk.LEFT)
        self.lbl_status = tk.Label(frm_bottom, text="模块未加载", anchor=tk.W)
        self.lbl_status.pack(side=tk.RIGHT)

        # 立即尝试加载模块（若存在）
        try:
            self.mod = load_encrypt_module(MODULE_PATH)
            self.lbl_status.config(text=f"模块已加载: {os.path.basename(MODULE_PATH)}")
        except Exception:
            self.mod = None
            self.lbl_status.config(text=f"模块未加载（点击加载）")
        # 窗口关闭时保存设置
        try:
            self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        except Exception:
            pass

        # 刷新最近菜单（初始化）
        self._refresh_recent_menu()

        # （删除：这些内容应在 __init__ 方法体外，不应存在）

    def _on_load_module(self):
        try:
            self.mod = load_encrypt_module(MODULE_PATH)
            self.lbl_status.config(text=f"模块已加载: {os.path.basename(MODULE_PATH)}")
            messagebox.showinfo("模块加载", "加密模块加载成功")
        except Exception as e:
            self.mod = None
            self.lbl_status.config(text="模块加载失败")
            messagebox.showerror("加载失败", f"加载模块失败：{e}\n{traceback.format_exc()}")

    def _on_toggle_remember(self):
        self.settings.remember_password = bool(self.var_remember.get())
        if not self.settings.remember_password:
            # 清除保存的密码
            self.settings.password = ''
        else:
            # 保存当前密码
            self.settings.password = self.entry_password.get()
        self.settings.save()

    def _on_select_recent(self, value: str):
        # 下拉选择了最近的文件，尝试加载到输入框
        if not value:
            return
        try:
            if os.path.exists(value):
                with open(value, 'r', encoding='utf-8') as f:
                    self.txt_input.delete(1.0, tk.END)
                    self.txt_input.insert(tk.END, f.read())
                self.lbl_status.config(text=f"已从最近文件加载: {os.path.basename(value)}")
                # 将该文件移动到最近首位并保存
                self.settings.add_recent(value)
                self._refresh_recent_menu()
            else:
                messagebox.showwarning("文件不存在", f"最近文件已不存在: {value}")
        except Exception as e:
            messagebox.showerror("加载失败", f"无法加载最近文件：{e}")

    def _refresh_recent_menu(self):
        # 重新填充最近文件下拉菜单，保证至少有一个选项
        menu = self.opt_recent['menu']
        menu.delete(0, 'end')
        recent_list = self.settings.recent_files if self.settings.recent_files else ['']
        for fpath in recent_list:
            menu.add_command(label=fpath, command=lambda v=fpath: self.var_recent.set(v) or self._on_select_recent(v))
        # 保证变量值合法
        if self.var_recent.get() not in recent_list:
            self.var_recent.set(recent_list[0])

    def _load_from_file(self):
        p = filedialog.askopenfilename(title="选择要加载的文本文件", filetypes=[("Text files", "*.txt;*.md;*.*")])
        if not p:
            return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                self.txt_input.delete(1.0, tk.END)
                self.txt_input.insert(tk.END, f.read())
                self.lbl_status.config(text=f"已从文件加载: {os.path.basename(p)}")
                # 更新最近文件列表
                self.settings.add_recent(p)
                self._refresh_recent_menu()
        except Exception as e:
            messagebox.showerror("读取失败", f"无法读取文件：{e}")

    def _save_output_to_file(self):
        p = filedialog.asksaveasfilename(title="保存 Token 到文件", defaultextension='.txt', filetypes=[('Text','*.txt')])
        if not p:
            return
        try:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(self.txt_output.get(1.0, tk.END))
            self.lbl_status.config(text=f"已保存到: {os.path.basename(p)}")
            # 将保存路径加入最近文件
            self.settings.add_recent(p)
            self._refresh_recent_menu()
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存文件：{e}")

    def _copy_output(self):
        txt = self.txt_output.get(1.0, tk.END).strip()
        if not txt:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(txt)
        self.lbl_status.config(text="已复制到剪贴板")

    def _run_encrypt(self):
        if not self.mod:
            messagebox.showwarning("模块未加载", "请先加载或确保同目录下存在 `1.py` 模块")
            return
        password = self.entry_password.get()
        if password == "":
            messagebox.showwarning("缺少密码", "请输入密码")
            return
        plaintext = self.txt_input.get(1.0, tk.END).rstrip('\n')
        def work():
            try:
                token = self.mod.encrypt(password, plaintext)
                self.txt_output.delete(1.0, tk.END)
                self.txt_output.insert(tk.END, token)
                self.lbl_status.config(text="加密成功")
            except Exception as e:
                self.lbl_status.config(text="加密失败")
                messagebox.showerror("加密失败", f"错误：{e}\n{traceback.format_exc()}")
        threading.Thread(target=work, daemon=True).start()

    def _run_decrypt(self):
        if not self.mod:
            messagebox.showwarning("模块未加载", "请先加载或确保同目录下存在 `1.py` 模块")
            return
        password = self.entry_password.get()
        if password == "":
            messagebox.showwarning("缺少密码", "请输入密码")
            return
        token = self.txt_input.get(1.0, tk.END).strip()
        def work():
            try:
                plaintext = self.mod.decrypt(password, token)
                self.txt_output.delete(1.0, tk.END)
                self.txt_output.insert(tk.END, plaintext)
                self.lbl_status.config(text="解密成功")
            except Exception as e:
                self.lbl_status.config(text="解密失败")
                messagebox.showerror("解密失败", f"错误：{e}\n{traceback.format_exc()}")
        threading.Thread(target=work, daemon=True).start()


def main():
    root = tk.Tk()
    app = CryptoGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
