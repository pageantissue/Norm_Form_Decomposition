from itertools import combinations
import sqlite3

global _3NF_Box
_3NF_Box = list()


class TNF_Relation:
    def __init__(self, attributes, fds):
        self.attributes = attributes
        self.fds = fds
        self.conn = sqlite3.connect('closure.db')
        self.cursor = self.conn.cursor()
        self.create_closure_table()
        self.add_dependency()
        self.candidate_keys = self.get_candidate_keys()

    def __repr__(self):
        relation_str = " ".join(self.attributes)
        fd_str = "\n\t\t".join(self.generate_fds_for_cover())
        parts = [f"\n表格属性: ( {relation_str} )", f"\n函数依赖:\n\t\t{fd_str}\n"]
        parts = "".join(parts)
        return parts

    def calculate_fd_closure(self):
        attrs = self.attributes
        fd_list = self.generate_fds_for_cover()

        def all_lhs(s, j):
            if j == len(attrs):
                if len(s) > 0:
                    LHS.append(s)
            else:
                all_lhs(s, j + 1)
                s += attrs[j]
                all_lhs(s, j + 1)

        def fd_closure():
            ret = []
            for this_lhs in LHS:
                s = this_lhs + "->"
                this = ''.join(closure(this_lhs, fd_list))  # 这里调用的是求属性闭包的函数，将其返回的属性列表转为字符串
                s += this
                ret.append(s)
            return ret

        LHS = []
        all_lhs("", 0)
        ans = fd_closure()
        return ans

    def create_closure_table(self):
        self.cursor.execute("DROP TABLE IF EXISTS functional_dependencies")
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS functional_dependencies
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               lhs TEXT,
                               rhs TEXT)''')
        self.conn.commit()

    def add_dependency(self):
        for fd in self.fds:
            lhs = "".join(fd[0])
            rhs = "".join(fd[1])
            self.cursor.execute('''INSERT INTO functional_dependencies (lhs, rhs)
                              VALUES (?, ?)''', (','.join(lhs), ','.join(rhs)))
            self.conn.commit()
            self.cursor.execute('''SELECT lhs, rhs FROM functional_dependencies''')
            self.conn.commit()

    def get_closure(self, attributes):
        temp_closure = set([at for at in attributes])
        # Initialize closure with the input attributes
        while True:
            change = False
            # Iterate over each functional dependency
            self.cursor.execute('''SELECT lhs, rhs FROM functional_dependencies''')
            dependencies = self.cursor.fetchall()
            for lhs, rhs in dependencies:
                lhs = lhs.split(',')
                rhs = rhs.split(',')
                # Check if the left-hand side of the dependency is a subset of the closure
                if set(lhs).issubset(temp_closure):
                    # Add the right-hand side of the dependency to the closure
                    new_attributes = set(rhs) - temp_closure
                    if new_attributes:
                        temp_closure |= new_attributes
                        change = True

            if not change:
                break

        return temp_closure

    def get_multi_attr_closure(self, attr):
        fd_list = self.get_Canonical_Cover()
        if isinstance(attr, list):
            attr = ''.join(attr)
        my_closure = closure(attr, fd_list)
        joined_str = ''.join(my_closure)  # 将列表元素连接成一个字符串
        unique_chars = list(set(joined_str))  # 去除重复字符并转换为列表
        return unique_chars

    def is_super_key(self, attr):
        return set(self.get_closure(attr)) == set(self.attributes)

    def get_candidate_keys(self):
        candidate_keys = []
        sorted_power_set = powerset(self.attributes)
        for set_ in sorted_power_set:
            attrs = [a for a in set_]
            flag = False
            # attrs = ''.join(attrs)
            if self.is_super_key(attrs):
                if not candidate_keys:  # 目前一个超码都没有
                    candidate_keys.append(attrs)
                else:
                    for candidate_key in candidate_keys:
                        cur_key = [char for char in candidate_key]
                        obj_key = [char for char in attrs]
                        if set(cur_key).issubset(set(obj_key)):
                            # 发现不是最小的超码
                            flag = True
                            break
                    # 当前超码不是最小超码，跳过该key
                    if flag:
                        continue
                    candidate_keys.append(attrs)
        return candidate_keys

    def generate_fds_for_cover(self):
        my_fds = self.get_fds()
        my_ans = list()
        ptr = '->'
        for Tuple in my_fds:
            lhs_list = Tuple[0]
            rhs_list = Tuple[1]
            lhs = "".join(lhs_list)
            rhs = "".join(rhs_list)
            parts = [lhs, ptr, rhs]
            fd = ''.join(parts)
            my_ans.append(fd)
        return my_ans

    def get_Canonical_Cover(self):
        fd_list = self.generate_fds_for_cover()
        fd_list = duplicate(decomposition(fd_list))
        fd_list = duplicate(removeExtraFD(fd_list))
        fd_list = duplicate(removeExtraAttribute(fd_list))
        fd_list = duplicate(composition(fd_list))
        return fd_list

    def set_fds_for_Canonical_Cover(self):
        cover = self.get_Canonical_Cover()
        new_fds = list()
        for fd in cover:
            new_fd = (list(fd.split('->')[0]), list(fd.split('->')[1]))
            new_fds.append(new_fd)
        return new_fds

    def get_fds(self):
        self.cursor.execute('''SELECT DISTINCT lhs, rhs FROM functional_dependencies''')
        dependencies = self.cursor.fetchall()
        fds = [(lhs.split(','), rhs.split(',')) for lhs, rhs in dependencies]
        return fds

    def check_3nf(self):
        fds = self.set_fds_for_Canonical_Cover()
        attributes = self.attributes
        sss = '\n检查正则覆盖中函数依赖: ...'
        _3NF_Box.append(sss)
        flag = True
        this_i = 0
        for lhs, rhs in fds:
            this_i += 1
            sss = f"\n{this_i}: {''.join(sorted(lhs))} -> {''.join(sorted(rhs))}"
            _3NF_Box.append(sss)
            attr_str = f'{lhs}->{rhs}'
            this_closure = self.get_multi_attr_closure(attr_str)
            converted_closure = []
            for x_i in this_closure:
                for ch in x_i:
                    if ch.isalpha():
                        converted_closure.append(ch)
            converted_closure = "".join(converted_closure)
            sss = f"左侧属性 {''.join(sorted(lhs))} 的闭包为: {''.join(sorted(converted_closure))}"
            _3NF_Box.append(sss)
            if not set(rhs).issubset(set(attributes)):
                sss = f"输入异常: 右侧属性 {''.join(sorted(rhs))} 中存在不属于您输入的关系 {attributes} ！"
                _3NF_Box.append(sss)
                return False

            if check_trivial_fds([lhs, rhs]):
                sss = f"检查函数依赖平凡性: 函数依赖: {''.join(sorted(lhs))} -> {''.join(sorted(rhs))} 是一个平凡函数依赖, 没有破坏第三范式，跳过对该函数依赖的后续测试..."
                _3NF_Box.append(sss)
                continue
            else:
                sss = "检查函数依赖平凡性: 该函数依赖是非平凡的。"
                _3NF_Box.append(sss)

            if self.is_super_key(lhs):
                sss = f"结合该表格的候选码，函数依赖左侧属性: {''.join(sorted(lhs))} 是原表格的超键，没有破坏第三范式，跳过对该函数依赖的后续测试..."
                _3NF_Box.append(sss)
                continue
            else:
                sss = f"函数依赖左侧属性: {''.join(sorted(lhs))} 不是原表格的超键..."
                _3NF_Box.append(sss)

            # 检查 rhs - lhs 中的每个属性是否都包含在候选键 candidate_keys 中
            diff_set = list(set(rhs) - set(lhs))
            can_ = self.candidate_keys
            new_candidate = list()
            for can_set in can_:
                can_list = list(can_set)
                new_candidate.append("".join(can_list))
            bool_list = [any(char in string for string in new_candidate) for char in diff_set]
            is_contained = all(bool_list)

            if is_contained:
                sss = f"右侧属性 {''.join(sorted(rhs))} 与左侧属性 {''.join(sorted(lhs))} 的差集为 {diff_set}, 其中的每一个元素都出现在了候选码中...\n函数依赖 {''.join(sorted(lhs))} -> {''.join(sorted(rhs))} 没有破坏第三范式。"
                _3NF_Box.append(sss)
                continue
            else:
                obj_idx = bool_list.index(False)
                obj = diff_set[obj_idx]
                sss = f"函数依赖 RHS —— LHS = {obj} 没有出现在候选码中...\n该函数依赖破坏第三范式"
                _3NF_Box.append(sss)
                flag = False

        if flag:
            sss = '\n（正则覆盖内）所有函数依赖均未破坏第三范式\n'
            _3NF_Box.append(sss)
            return True
        else:
            return flag

    def decompose_to_3nf(self):
        fds_ = self.set_fds_for_Canonical_Cover()
        new_relations = []
        all_c = self.candidate_keys
        _3NF_Box.append('\n')
        for fd in fds_:
            lhs = fd[0]
            rhs = fd[1]
            this_relation = set(lhs) | set(rhs)
            new_relations.append(sorted(this_relation))
            sss = f"创建子表: {set(sorted(this_relation))} (为了保存函数依赖: {''.join(sorted(lhs))}->{''.join(sorted(rhs))})"
            _3NF_Box.append(sss)

        flag = False
        Can_Key = [''.join(keys) for keys in self.candidate_keys]
        Can_Set = set(Can_Key)
        for new_r in new_relations:
            A = ''.join(new_r)
            for C_K in Can_Set:
                if set(C_K).issubset(set(A)):
                    flag = True
                    break
        if not flag:
            size = len(all_c)
            temp_c = all_c[size - 1]
            new_relations.append(temp_c)
            sss = f"由于现已分解的所有子表中没有包含任何原表格的候选码，为了确保分解后的关系仍然能够保持数据的完整性和一致性，并能够准确地标识和区分每个元组，我们将原表格任一候选码作为一个子表\n创建子表: {set(temp_c)}"
            _3NF_Box.append(sss)
            all_c.pop(size - 1)

        return new_relations

        new_relations = remove_subsets(new_relations)
        sss = '\n\n最终结果:'
        _3NF_Box.append(sss)
        return new_relations


def powerset(s):
    return [set(ss) for r in range(len(s) + 1) for ss in combinations(s, r)]


def remove_subsets(lst):
    new_lst = []
    for i in range(len(lst)):
        is_subset = False
        for j in range(len(lst)):
            if i != j and lst[i].issubset(lst[j]):
                is_subset = True
                break
        if not is_subset:
            new_lst.append(lst[i])
    return new_lst


def is_trivial_fd(fd):
    lhs, rhs = fd
    return set(rhs).issubset(set(lhs))


def check_trivial_fds(fd):
    if not is_trivial_fd(fd):
        return False
    return True


# 1) removing duplicate FD
def duplicate(newList):
    new = []
    for i in newList:
        if i not in new:
            new.append(i)
    return new


# 2) decomposition function
def decomposition(newList):
    decomposed_list = []
    for i in newList:
        splitfd = i.split("->")
        if len(splitfd[1]) > 1:
            extra = list(splitfd[1])
            for j in extra:
                decomposed_list.append("->".join([splitfd[0], j]))
        else:
            decomposed_list.append(i)
    return decomposed_list


# 3) finding Closure of FD
def closure(fd, fdList):  # fdList -> containing all FDs ,fd -> particular FD (attribute or set of attributes)
    fd = fd.split("->")
    attrClosure = []
    leftSide = []
    rightSide = []
    attrClosure += list(fd[0])  # every set of attribute can determine itself
    for i in fdList:
        leftSide.append(i.split("->")[0])
    for i in fdList:
        rightSide.append(i.split("->")[1])
    while True:  # for queue like
        prevClosure = attrClosure.copy()
        for value in range(len(leftSide)):  # all value of leftside in attrClosure
            if all(item in attrClosure for item in list(leftSide[value])):
                attrClosure += list(rightSide[value])
        attrClosure = duplicate(attrClosure)
        if prevClosure == attrClosure:
            return duplicate(attrClosure)


# 4) finding extraneous FD and removing it --> (i.e. only considering essential FD in final FDs)
def removeExtraFD(fdList):  # fdlist --> decomposed list
    for _ in fdList:
        for j in fdList:
            tempList = fdList.copy()
            tempList.remove(j)
            if sorted(closure(j, tempList)) == sorted(closure(j,
                                                              fdList)):  # if the closure changes by removing the FD , then it is essential otherwise redundant
                fdList.remove(j)
    return fdList


# 5) removing extra attributes
def removeExtraAttribute(fdList):
    for i in range(len(fdList)):
        fd = fdList[i].split("->")[0]  # leftside of FDs
        fd_value = fdList[i].split("->")[1]  # rightside of FDs
        if len(fd) > 1:
            for j in range(len(fd)):
                tempAttr = fd[:j] + fd[j + 1:]
                a = "->".join([tempAttr, fd_value])
                if (fd[j] in closure(tempAttr, fdList)) and (fdList[i] in fdList):
                    fdList.append(a)
                    fdList.remove(fdList[i])
    return fdList


# 6) Composition
def composition(fdList):
    for i in fdList:
        fd = i.split('->')
        tempList = []
        for j in fdList:
            fdTemp = j.split('->')
            if fd[0] == fdTemp[0] and (j not in tempList):
                tempList.append(j)

        if len(tempList) > 1:
            for t in tempList:
                fdList.remove(t)
            tempAttr = ""
            for k in tempList:
                temp = k.split("->")
                tempAttr += temp[1]
            new = temp[0] + "->" + tempAttr
            fdList.append(new)

    return fdList


fds = [[['A'], ['C']], [['B'], ['D']]]
# Create the relation object with attributes
relation = TNF_Relation(['A', 'B', 'C', 'D'], fds)

# print(relation.candidate_keys)
# # Check if the relation is in 3NF and decompose if necessary
# if not relation.check_3nf():
#     print("The relation is not in 3NF. Decomposing...")
#     decomposed_relations = relation.decompose_to_3nf()
#
#     for i, decomposed_relation in enumerate(decomposed_relations):
#         print(f"Decomposed Relation {i + 1}: {decomposed_relation}")
# else:
#     print("The relation is already in 3NF.")
# for x in _3NF_Box:
#     print(x)
