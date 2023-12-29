import sqlite3
from itertools import combinations

global BC_Box
BC_Box = list()
LHS = list()
RHS = []
res = []
finalRes = []
tempRes = []
midRes = []


def powerset(s):
    return [set(ss) for r in range(len(s) + 1) for ss in combinations(s, r)]


def issubset(s1, s2):
    return set(s2).issubset(set(s1))


def inter(a1, a2):
    return set(a1) & set(a2)


def uni(a1, a2):
    return set(a1) | set(a2)


def except_(a1, a2):
    return set(a1) - set(a2)


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


def check_lossless(attributes, re):
    attributes = set(attributes)
    temp_set = set(re[0])
    for i in range(len(re)):
        temp_set = temp_set.union(set(re[i]))

    return temp_set.issubset(attributes)


class BC_Relation:
    def __init__(self, attributes, FDs):
        self.loss_less = list()
        self.attributes = attributes
        self.fds = FDs
        self.relation = attributes
        self.conn = sqlite3.connect('closure.db')
        self.cursor = self.conn.cursor()
        self.create_closure_table()
        self.add_dependency()
        self.fds_left, self.fds_right = self.get_fds_separate()
        self.final, self.mid = [], []
        self.candidate_keys = self.get_candidate_keys()

    def __repr__(self):
        relation_str = " ".join(self.attributes)
        fd_str = "\n\t\t".join(self.generate_fds_for_cover())
        parts = [f"\n表格属性: ( {relation_str} )", f"\n函数依赖:\n\t\t{fd_str}\n"]
        parts = "".join(parts)
        return parts

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

    def get_fds(self):
        self.cursor.execute('''SELECT DISTINCT lhs, rhs FROM functional_dependencies''')
        dependencies = self.cursor.fetchall()
        this_fds = [(lhs.split(','), rhs.split(',')) for lhs, rhs in dependencies]
        return this_fds

    def get_candidate_keys(self):
        candidate_keys = []
        sorted_power_set = powerset(self.attributes)
        for set_ in sorted_power_set:
            attrs = [a for a in set_]
            # attrs = ''.join(attrs)
            if self.is_super_key(attrs):
                if not candidate_keys:  # 目前一个超码都没有
                    candidate_keys.append(attrs)
                else:
                    for candidate_key in candidate_keys:
                        cur_key = [char for char in candidate_key]
                        obj_key = [char for char in attrs]
                        if set(cur_key).issubset(set(obj_key)):
                            continue

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

    def get_fds_separate(self):
        all_fds = self.generate_fds_for_cover()
        my_lhs, my_rhs = [], []
        for fd in all_fds:
            fd = fd.split('->')
            my_lhs.append(fd[0])
            my_rhs.append(fd[1])
        return my_lhs, my_rhs

    def is_super_key(self, attr):
        return set(self.get_closure(attr)) == set(self.attributes)

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
                    if flag:
                        continue
                    candidate_keys.append(attrs)
        return candidate_keys

    def attr_closure(self, attr):
        a = set(attr)
        fds_left = self.fds_left
        fds_right = self.fds_right
        while True:
            size1 = len(a)
            for i in range(len(fds_left)):
                if issubset(a, fds_left[i]):
                    a |= set(fds_right[i])
            size2 = len(a)
            if size1 == size2:
                break
        return "".join(a)

    def fdClosure(self):
        global RHS
        RHS = [self.attr_closure(x) for x in LHS]

    def allLHS(self, s='', i=0):
        global LHS, relation
        relation = self.relation
        if i == len(relation):
            if s:
                LHS.append(s)
        else:
            self.allLHS(s + relation[i], i + 1)
            self.allLHS(s, i + 1)

    def check_bcnf(self):
        this_fds = self.generate_fds_for_cover()
        flag = True
        this_i = 0
        for fd in this_fds:
            this_i += 1
            sss = f'\n{this_i}.  {fd}'
            BC_Box.append(sss)
            fd = fd.split('->')
            lhs = fd[0]
            rhs = fd[1]

            if check_trivial_fds([lhs, rhs]):
                sss = '当前函数依赖是平凡函数依赖，可以跳过对该函数依赖的后续测试...'
                BC_Box.append(sss)
                continue
            else:
                sss = '这不是一个平凡函数依赖。'
                BC_Box.append(sss)

            if not self.is_super_key(lhs):
                flag = False
                sss = f'该函数依赖左侧属性 {"".join(sorted(lhs))} 不是当前表格的超键，破坏BC范式。'
                BC_Box.append(sss)
            else:
                sss = '该函数依赖没有破坏BC范式。'
                BC_Box.append(sss)

        if flag:
            sss = '经过判断，没有函数依赖破坏BC范式。'
            BC_Box.append(sss)
            return flag
        else:
            sss = '该表格不符合BC范式要求, 准备分解。\n'
            BC_Box.append(sss)
            self.final, self.mid = self.decompose_to_bcnf()
            return flag

    def get_Canonical_Cover(self):
        fd_list = self.generate_fds_for_cover()
        fd_list = duplicate(decomposition(fd_list))
        fd_list = duplicate(removeExtraFD(fd_list))
        fd_list = duplicate(removeExtraAttribute(fd_list))
        fd_list = duplicate(composition(fd_list))
        return fd_list

    def decompose(self, r):
        midRes.append(frozenset(r))
        global res
        flag = True
        for i in range(len(LHS)):
            a1 = set(LHS[i])
            a2 = set(RHS[i])
            if issubset(r, a1):
                if issubset(a2, r) or inter(a2, r) == a1:
                    sss = f"{LHS[i]}->{''.join(sorted(RHS[i]))}该依赖不破坏BCNF"
                    BC_Box.append(sss)
                    continue
                sss = f"{LHS[i]}->{''.join(sorted(RHS[i]))}该依赖破坏BCNF，当前的R为: {''.join(sorted(r))}"
                BC_Box.append(sss)
                flag = False
                r1 = uni(a1, inter(a2, r))
                r2 = except_(r, except_(a2, a1))
                sss = "将当前R分解为：" + ''.join(sorted(r1)) + '   ' + ''.join(sorted(r2)) + '\n'
                BC_Box.append(sss)
                self.decompose(r1)
                self.decompose(r2)
                break
        if flag:
            sss = f"经检查，当前R满足BCNF，当前R为{''.join(sorted(r))}, 将其加入最终结果"
            BC_Box.append(sss)
            res.append(frozenset(r))
            midRes.append(None)

    def decompose_to_bcnf(self):
        global res, finalRes
        self.allLHS()
        self.fdClosure()
        r = set(self.relation)
        sss = '使用函数依赖闭包并开始分解:...\n'
        BC_Box.append(sss)
        self.decompose(r)

        # 去重
        for i_ in res:
            if i_ not in tempRes:
                tempRes.append(i_)
        sss = "\n去除重复后的结果为:"
        BC_Box.append(sss)
        # 去包含
        for i_ in tempRes:
            flag = True
            for j in tempRes:
                if i_.issubset(j) and j != i_:
                    flag = False
                    break
            if flag:
                finalRes.append(i_)

        for i_ in finalRes:
            sss = f"{''.join(sorted(i_))}"
            BC_Box.append(sss)
        return finalRes, midRes

    def check_dependency_preserving(self, re):
        temp_fds = self.get_fds()
        for fd in temp_fds:
            lhs, rhs = set(fd[0]), set(fd[1])
            # 检查函数依赖的左边和右边是否都在至少一个分解的关系中
            if not any(lhs.issubset(set(r)) and rhs.issubset(set(r)) for r in re):
                return False
        return True

    def is_lossless(self):
        all_results = self.final
        flag = True

        # Iterating through each pair of decomposed relations
        for i in range(len(all_results)):
            for j in range(i + 1, len(all_results)):
                # Getting the intersection of two relations
                intersection = set(all_results[i]).intersection(set(all_results[j]))
                # Adding to BC_Box
                sss = f"检查子表{all_results[i]}和子表{all_results[j]}的交集: {intersection}\n"
                BC_Box.append(sss)

                # Checking if intersection is superkey in any of the two relations
                is_superkey_in_first = self.is_super_key_for_subrelation(list(intersection), all_results[i])
                is_superkey_in_second = self.is_super_key_for_subrelation(list(intersection), all_results[j])

                # Adding results of the check to BC_Box
                if is_superkey_in_first:
                    sss = f"该交集是子表{all_results[i]}的超码.\n"
                    BC_Box.append(sss)
                else:
                    sss = f"该交集不是子表{all_results[i]}的超码.\n"
                    BC_Box.append(sss)

                if is_superkey_in_second:
                    sss = f"该交集是子表{all_results[j]}的超码.\n"
                    BC_Box.append(sss)
                else:
                    sss = f"该交集不是子表{all_results[j]}的超码.\n"
                    BC_Box.append(sss)

                # If intersection is not superkey in any of the sub-relations, the decomposition is not lossless.
                if not is_superkey_in_first and not is_superkey_in_second:
                    flag = False
                    sss = "该分解是有损的.\n"
                    BC_Box.append(sss)

        # Adding the final result to BC_Box
        if flag:
            sss = "所有子表的交集都是其超码, 分解是无损的.\n"
            BC_Box.append(sss)

        self.loss_less = flag
        return self.loss_less

    def is_super_key_for_subrelation(self, attr, subrelation):
        # Check if a set of attributes is a superkey for a given subrelation
        return set(self.get_closure_for_subrelation(attr, subrelation)) == set(subrelation)

    def get_closure_for_subrelation(self, attributes, subrelation):
        # Function to get closure of attributes considering only the FDs within subrelation
        temp_closure = set(attributes)
        while True:
            change = False
            # Iterate over each functional dependency
            for lhs, rhs in self.fds:
                lhs_set = set(lhs)
                rhs_set = set(rhs)
                # Check if the left-hand side of the dependency is a subset of the closure
                # and the FD is within the subrelation
                if lhs_set.issubset(temp_closure) and lhs_set.issubset(subrelation) and rhs_set.issubset(subrelation):
                    # Add the right-hand side of the dependency to the closure
                    new_attributes = rhs_set - temp_closure
                    if new_attributes:
                        temp_closure |= new_attributes
                        change = True
            if not change:
                break
        return temp_closure


def is_trivial_fd(fd):
    lhs, rhs = fd
    return set(rhs).issubset(set(lhs))


def check_trivial_fds(fd):
    if not is_trivial_fd(fd):
        return False
    return True


# fds = [[['A'], ['B']], [['B'], ['C', 'D']]]
# # Create the relation object with attributes
# _relation = BC_Relation(['A', 'B', 'C', 'D'], fds)
#
# print(_relation.candidate_keys)
# if not _relation.check_bcnf():
#     print("The relation is not in BCNF. Decomposing...")
#     decomposed_relations = _relation.final
#
#     for i, decomposed_relation in enumerate(decomposed_relations):
#         print(f"Decomposed Relation {i + 1}: {decomposed_relation}")
# else:
#     print("The relation is already in BCNF.")
# for x in BC_Box:
#     print(x)
