import tkinter as tk
import re
from tkinter import messagebox
from ThirdNF_source import TNF_Relation, _3NF_Box
from BC_source import BC_Relation, BC_Box
import datetime
import os

global relation_BC


class TreeNode:
    def __init__(self, value):
        self.value = ', '.join(sorted(value))
        self.left = None
        self.right = None


def convert(lhs):
    ans = lhs
    if ',' in ans:
        ans = ans.split(',')
        ans = "".join(ans)
    if ' ' in ans:
        ans = ans.split(' ')
        ans = "".join(ans)
    ans = [char.upper() for char in ans]
    return ans


def normalize_input(r_value):
    ans = r_value
    if ' ' in ans:
        ans = ans.split(' ')
        ans = "".join(ans)
    if ',' in ans:
        ans = ans.split(',')
        ans = "".join(ans)
    t_ = []
    for chars in ans:
        for char in chars:
            t_.append(char.upper())
    return t_


def get_FDs(f_list):
    FDs = list()
    for fd in f_list:
        lhs, rhs = fd[0], fd[1]
        lhs, rhs = convert(lhs), convert(rhs)
        FD = [lhs, rhs]
        FDs.append(FD)
    return FDs


my_num3NF = 0
my_numBC = 0


def main():
    # 创建主窗口并命名
    root = tk.Tk()
    root.title("3NF&BCNF范式分解小工具")

    # 此处设置窗口大小、背景颜色并且锁定界面尺寸不得改变
    root.geometry("800x600")
    root.configure(bg="#F7D9AA")
    root.resizable(False, False)

    # 创建标签和文本框用于输入关系模式R
    r_label = tk.Label(root, text="请输入关系模式 R：", font=("Arial", 18), bg='#F7D9AA')
    r_label.place(relx=0.3, rely=0.2, anchor="center")
    r_entry = tk.Entry(root, font=("Arial", 16), width=50)
    r_entry.place(relx=0.5, rely=0.25, anchor="center")

    # 创建标签和文本框用于输入函数依赖集合F
    f_label = tk.Label(root, text="请输入函数依赖集合 F：", font=("Arial", 18), bg='#F7D9AA')
    f_label.place(relx=0.3, rely=0.4, anchor="center")
    f_entry = tk.Entry(root, font=("Arial", 16), width=50)
    f_entry.place(relx=0.5, rely=0.45, anchor="center")

    # 添加说明标签
    explanation_label = tk.Label(root, text="(注：可以输入字符和逗号 系统不区分字母大小写，统一用大写展示)",
                                 font=("Arial", 14),
                                 bg='#F7D9AA')
    explanation_label.place(relx=0.5, rely=0.6, anchor="center")
    explanation_label = tk.Label(root, text="(注：多个函数依赖集请使用|隔开，如：A->B|C,D->E)", font=("Arial", 14),
                                 bg='#F7D9AA')
    explanation_label.place(relx=0.5, rely=0.65, anchor="center")
    # 这里是回调函数，在点击提交按钮后获取输入的R与F
    # 定义正则表达式，只允许输入大写字母、逗号、竖线和箭头
    regex = r'^[ a-z, A-Z ,| \ ->]+$'

    # get_input1()负责处理3NF分解
    def get_input1() -> list:
        r_value = r_entry.get()
        f_value = f_entry.get()

        # 判断输入是否符合规定的正则表达式
        if not re.match(regex, r_value) or not re.match(regex, f_value):
            # 如果不符合，弹出提示框
            tk.messagebox.showerror("错误", "仅允许输入字母、逗号、竖线、空格和'->'。")
            return [None]

        attributes = normalize_input(r_value)
        # 创建函数依赖列表
        f_list = []
        # 以|分隔每个函数依赖
        fds = f_value.split('|')
        # 以箭头分隔函数依赖关系的两侧并且填入函数依赖列表
        for fd in fds:
            new_fds = fd.split('->')
            f_list.append(new_fds)

        if attributes is not None and fds is not None:
            attributes = [char.upper() for char in attributes]
            FDs = get_FDs(f_list)
            relation = TNF_Relation(attributes, FDs)
            _3NF_Box.append('已经将用户输入字符全部更改为大写！')
            parts = ['得到关系模式：', relation.__repr__()]
            _3NF_Box.append("".join(parts))
            parts = [f'函数依赖集合的正则覆盖为: {"; ".join(relation.get_Canonical_Cover())}',
                     f"\n当前关系模式的候选码为: {','.join([''.join(sorted(list_)) for list_ in relation.candidate_keys])}"]
            _3NF_Box.append("".join(parts))

            if not relation.check_3nf():
                decomposed_relations = relation.decompose_to_3nf()

                for i, decomposed_relation in enumerate(decomposed_relations):
                    sss = f"分解子表 {i + 1}: {''.join(sorted(decomposed_relation))}"
                    _3NF_Box.append(sss)
                _3NF_Box.append('\n\n分解已完成。')
            else:
                sss = "\n输入关系在当前函数依赖下符合第三范式。"
                _3NF_Box.append(sss)

    # get_input2()负责处理BCNF分解
    def get_input2() -> list:
        r_value = r_entry.get()
        f_value = f_entry.get()

        # 判断输入是否符合规定的正则表达式
        if not re.match(regex, r_value) or not re.match(regex, f_value):
            # 如果不符合，弹出提示框
            tk.messagebox.showerror("错误", "仅允许输入字母、逗号、竖线、空格和'->'。")
            return [None]

        attributes = normalize_input(r_value)
        # 创建函数依赖列表
        f_list = []
        # 以|分隔每个函数依赖
        fds = f_value.split('|')
        # 以箭头分隔函数依赖关系的两侧并且填入函数依赖列表
        for fd in fds:
            new_fds = fd.split('->')
            f_list.append(new_fds)

        # 大概从这里开始修改为处理BCNF的代码...

        if attributes is not None and fds is not None:
            attributes = [char.upper() for char in attributes]
            FDs = get_FDs(f_list)
            global relation_BC
            relation_BC = BC_Relation(attributes, FDs)
            BC_Box.append('已经将用户输入字符全部更改为大写！')
            parts = ['得到关系模式：', relation_BC.__repr__()]
            BC_Box.append("".join(parts))
            parts = [f'函数依赖集合的正则覆盖为: {"; ".join(relation_BC.get_Canonical_Cover())}',
                     f"\n当前关系模式的候选码为: {[''.join(sorted(list_)) for list_ in relation_BC.candidate_keys]}"]
            BC_Box.append("".join(parts))

            if not relation_BC.check_bcnf():
                decomposed_relations = relation_BC.final

                for i, decomposed_relation in enumerate(decomposed_relations):
                    sss = f"分解子表 {i + 1}: {''.join(sorted(decomposed_relation))}"
                    BC_Box.append(sss)
                BC_Box.append('\n\n分解已完成。')
            else:
                sss = "\n输入关系在当前函数依赖下符合第三范式。"
                BC_Box.append(sss)

    def show_window2_3NF():
        global my_num3NF
        my_num3NF += 1
        result_window = tk.Toplevel()
        result_window.title("3NF范式分解")
        result_window.geometry('1080x720')
        result_window.config(bg="#F7D9AA")
        result_window.resizable(True, True)

        scrollbar = tk.Scrollbar(result_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text = tk.Text(result_window, yscrollcommand=scrollbar.set, font=("Arial", 16), bg="#F7D9AA")
        text.tag_configure("new_line", foreground="blue")
        text.config(bg='#F7D9AA')
        text.insert("1.0", "\t\t\t    范式分解已完成，请点击按钮查看过程\n\n", "new_line")
        text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)

        def print_data(i):
            def save_results(result_this):
                if len(result_this) == 0:
                    return
                now = datetime.datetime.now()
                time_str = now.strftime("%m_%d")

                filename = f"3NF_decompose_result{my_num3NF}_{time_str}.txt"
                if os.path.exists(filename):
                    messagebox.showerror("保存失败", "同名文件已存在，您可能已经保存过该结果。")
                else:
                    with open(filename, 'w') as file:
                        for line in result_this:
                            file.write(line + '\n')

                    messagebox.showinfo("保存成功", f"结果已成功保存到文件：{filename}")
                _3NF_Box.clear()

            button.config(state=tk.DISABLED)  # 禁用按钮
            if i < len(_3NF_Box):
                item = _3NF_Box[i]
                text.insert(tk.END, item + '\n')
                result_window.after(1100, print_data, i + 1)
            else:
                result = _3NF_Box.copy()
                _3NF_Box.clear()
                button.config(state=tk.DISABLED)
                button.config(text="已保存结果到txt", command=save_results(result))  # 修改按钮文本和命令

        button = tk.Button(result_window, text="查看结果", command=lambda: print_data(0), font=("SimSun", 18),
                           bg='#FFA07A')
        button.pack(fill=tk.BOTH, expand=True)

        button_top = tk.Button(result_window, text="到达顶部", command=lambda: text.yview_moveto(0),
                               font=("SimSun", 18))
        button_top.config(bg='#4CAF50', fg='#FFFFFF')
        button_top.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        button_bottom = tk.Button(result_window, text="到达底部", command=lambda: text.yview_moveto(1),
                                  font=("SimSun", 18))
        button_bottom.config(bg='#2196F3', fg='#FFFFFF')
        button_bottom.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def show_window2_BCNF():
        parent_stack = []

        def list_to_tree(midRes):
            parent_stack.append(TreeNode(midRes[0]))
            for value in midRes:
                if midRes[0] == value:
                    continue
                if value is None:
                    parent_stack.pop()
                else:
                    node = TreeNode(value)
                    if parent_stack:
                        parent = parent_stack[-1]
                        if parent.left is None:
                            parent.left = node
                        elif parent.right is None:
                            parent.right = node
                        else:
                            parent_stack.pop()
                            parent = parent_stack[-1]
                            if parent.left is None:
                                parent.left = node
                            else:
                                parent.right = node
                    parent_stack.append(node)
            return parent_stack[0] if parent_stack else None

        def draw_node(canvas_here, tree_here, x=400, y=20, dx=200, dy=80, font_size_here=12):
            if tree_here is None:
                return

            node_width = max(40, 15 * len(str(tree_here.value)))
            node_height = 40

            # Yield node to draw it later
            yield tree_here, x, y, node_width, node_height

            # Recursive draw left and right
            for is_left, child in [(True, tree_here.left), (False, tree_here.right)]:
                if child:
                    factor = -1 if is_left else 1
                    child_x = x + factor * dx // 1.5
                    child_y = y + dy
                    yield from draw_node(canvas_here, child, child_x, child_y, dx // 2, font_size_here=font_size_here)

        draw_stack = []  # Initialize the draw_stack here

        def draw_next_node(root_here, canvas_here, node_generator_here):
            try:
                node, x, y, node_width, node_height = next(node_generator_here)

                # Draw oval
                oval = canvas_here.create_oval(x - node_width // 2, y - node_height // 2, x + node_width // 2,
                                               y + node_height // 2,
                                               fill='blue')

                # Insert text
                canvas_here.create_text(x, y, text=str(node.value), fill='white', font=("Arial", font_size))

                # Check if the draw_stack is not empty
                if draw_stack:
                    # Peek the parent info from the draw_stack
                    parent_x, parent_y, parent_node_width, parent_node_height, parent_node = draw_stack[-1]

                    # Check if this node is a left or right child
                    is_left = parent_node.left == node
                    is_right = parent_node.right == node

                    # If it's the right child, we can pop the parent info as it won't have more children
                    if is_right:
                        draw_stack.pop()

                    # Draw the line to the parent
                    line_x = parent_x
                    line_y = parent_y + parent_node_height // 2
                    canvas.create_line(line_x, line_y, x, y - node_height // 2, fill='black', width=2)
                else:
                    # If stack is empty, this is the root. So we don't have to draw any line.
                    pass

                # If this node has a left child, add it to stack
                if node.left or node.right:
                    draw_stack.append((x, y, node_width, node_height, node))

                root_here.update()
            except StopIteration:
                pass

        global my_numBC
        my_numBC += 1
        result_window = tk.Toplevel()
        result_window.title("BCNF分解图示")
        result_window.geometry('950x950')
        result_window.config(bg="#F7D9AA")
        result_window.resizable(True, True)
        global relation_BC
        tree = list_to_tree(relation_BC.mid)
        canvas = tk.Canvas(result_window, width=800, height=800, bg='white')
        canvas.pack()
        font_size = 14
        node_generator = draw_node(canvas, tree, font_size_here=font_size)
        draw_button = tk.Button(result_window, text="下一步",
                                command=lambda: draw_next_node(result_window, canvas, node_generator),
                                font=("Arial", 16),  # 设置字体和大小
                                height=1, width=6)  # 设置按钮的高度和宽度
        draw_button.pack()

        result_window1 = tk.Toplevel()
        result_window1.geometry('1080x720')
        result_window1.config(bg="#F7D9AA")
        result_window1.resizable(True, True)
        result_window1.title("BC范式分解详细信息")
        scrollbar = tk.Scrollbar(result_window1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text = tk.Text(result_window1, yscrollcommand=scrollbar.set, font=("Arial", 16), bg="#F7D9AA")
        text.tag_configure("new_line", foreground="blue")
        text.config(bg='#F7D9AA')
        text.insert("1.0", "\t\t\t    范式分解已完成，请点击按钮查看过程\n\n", "new_line")
        text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        button = tk.Button(result_window1, text="查看结果", command=lambda: print_data(0), font=("SimSun", 18),
                           bg='#FFA07A')
        button.pack(fill=tk.BOTH, expand=True)

        button_top = tk.Button(result_window1, text="到达顶部", command=lambda: text.yview_moveto(0),
                               font=("SimSun", 18))
        button_top.config(bg='#4CAF50', fg='#FFFFFF')
        button_top.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        button_bottom = tk.Button(result_window1, text="到达底部", command=lambda: text.yview_moveto(1),
                                  font=("SimSun", 18))
        button_bottom.config(bg='#2196F3', fg='#FFFFFF')
        button_bottom.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        def print_data(i):
            def save_results(result_this):
                if len(result_this) == 0:
                    return
                now = datetime.datetime.now()
                time_str = now.strftime("%m_%d")

                filename = f"BC_decompose_result{my_numBC}_{time_str}.txt"
                if os.path.exists(filename):
                    messagebox.showerror("保存失败", "同名文件已存在，您可能已经保存过该结果。")
                else:
                    with open(filename, 'w') as file:
                        for line in result_this:
                            file.write(line + '\n')

                    messagebox.showinfo("保存成功", f"结果已成功保存到文件：{filename}")
                BC_Box.clear()

            button.config(state=tk.DISABLED)  # 禁用按钮
            if i < len(BC_Box):
                item = BC_Box[i]
                text.insert(tk.END, item + '\n')
                result_window.after(1100, print_data, i + 1)
            else:
                result = BC_Box.copy()
                BC_Box.clear()
                button.config(state=tk.DISABLED)
                button.config(text="已保存结果到txt", command=save_results(result))  # 修改按钮文本和命令、

    # 添加提交按钮
    submit_button = tk.Button(root, text="分解为3NF", font=("Arial", 18), bg='#FFA07A', fg='white', width=10,
                              command=lambda: (get_input1(), show_window2_3NF()))
    submit_button.place(relx=0.5, rely=0.8, anchor="se")

    # 添加提交按钮
    submit_button2 = tk.Button(root, text="分解为BCNF", font=("Arial", 18), bg='#FFA07A', fg='white', width=10,
                               command=lambda: (get_input2(), show_window2_BCNF()))
    submit_button2.place(relx=0.5, rely=0.8, anchor="sw")
    root.mainloop()
