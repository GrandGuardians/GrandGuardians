# Tkinter 库
import tkinter as tk
from tkinter import messagebox

# 名单列表
names = ["白珩", "丹枫", "镜流", "应星", "景元"]

# 移除名单中的最后一个元素
def remove_last_name():
	if len(names) > 1:
		removed = names.pop()
		listbox.delete(tk.END)
		messagebox.showinfo("移除成功", f"已移除：{removed}")
	elif len(names) == 1:
		messagebox.showinfo("提示", f"只剩最后一个成员：{names[0]}，无法再移除！")
	else:
		messagebox.showwarning("名单为空", "名单已经全部移除！")

# 创建主窗口
root = tk.Tk()
root.title("云上五骁")

# 创建 Listbox 显示名单
listbox = tk.Listbox(root, width=30, height=6)
for name in names:
	listbox.insert(tk.END, name)
listbox.pack(pady=10)

# 创建按钮
remove_btn = tk.Button(root, text="移除最后一个成员", command=remove_last_name)
remove_btn.pack(pady=5)

# 运行主循环
root.mainloop()
