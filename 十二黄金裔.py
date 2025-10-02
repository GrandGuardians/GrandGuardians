# Tkinter 库
import tkinter as tk
from tkinter import messagebox

if __name__ == "__main__":
    # 定义两个列表
    def pair_lists(a, b):
        paired = list(zip(a, b))
        return a, b, paired
    names = ["荒笛","海瑟音","雅辛忒丝","赛法利娅","阿那刻萨戈拉斯","迈德漠斯","缇里西庇俄丝","遐蝶","阿格莱雅","刻律德菈","昔涟","卡厄斯兰那"]
    huozhong = ["'大地'的火种","'海洋'的火种","'天空'的火种","'诡计'的火种","'理性'的火种","'纷争'的火种","'门径'的火种","'死亡'的火种","'浪漫v","'律法'的火种","'岁月'的火种","'负世'的火种"]
    
    # 获取处理结果
    original_names, original_huozhong, name_huozhong_pairs = pair_lists(names, huozhong)

# 移除名单中的最后一个元素
def remove_last_huozhong():
	if len(huozhong) >= 1:
		removed = huozhong.pop()
		listbox.delete(tk.END)
		messagebox.showinfo("提示", f"{removed}已收集")
	else:
		messagebox.showwarning("提示", "12火种收集完毕，再创世即将开始")

# 创建主窗口
root = tk.Tk()
root.title("33550337")

# 创建 Listbox 显示名单
listbox = tk.Listbox(root, width=50, height=13)
for name in names:
	listbox.insert(tk.END, name)
listbox.pack(pady=10)

# 创建按钮
remove_btn = tk.Button(root, text="征伐泰坦", command=remove_last_huozhong)
remove_btn.pack(pady=5)

# 运行主循环
root.mainloop()