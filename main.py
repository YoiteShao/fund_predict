import pandas as pd
import math
import os
from matplotlib import pyplot as plt


# p_dic = {previous_tuple:{next_tuple:Int, ...}, ...}
# polymorphic_p_dic = {size:p_dic, ...}
def softmax_p_dic_value(dic):
    for _tuple in dic:
        _sum = 0
        for _tuple_behind in dic[_tuple]:
            _sum += math.exp(dic[_tuple][_tuple_behind])
        for _tuple_behind in dic[_tuple]:
            dic[_tuple][_tuple_behind] = math.exp(dic[_tuple][_tuple_behind]) / _sum
    return dic


def merge_next_tuple(dic1, dic2):
    grouping_dic = dict()
    for key in dic1.keys() | dic2.keys():
        grouping_dic[key] = sum([dic.get(key, 0) for dic in (dic1, dic2)])
    return grouping_dic


def merge_previous_tuple(dic1, dic2):
    combine_result = dict()
    for key in dic1.keys() | dic2.keys():
        if key in dic1 and key not in dic2:
            combine_result[key] = dic1[key]
        elif key not in dic1 and key in dic2:
            combine_result[key] = dic2[key]
        elif key in dic1 and key in dic2:
            combine_result[key] = merge_next_tuple(dic1[key], dic2[key])
        else:
            print("impossible")
    return softmax_p_dic_value(combine_result)


def merge_polymorphism_p_dic(dic1, dic2):
    merge_p_dic = {}
    for key in dic1.keys() | dic2.keys():
        if key in dic1 and key not in dic2:
            merge_p_dic[key] = dic1[key]
        elif key not in dic1 and key in dic2:
            merge_p_dic[key] = dic2[key]
        elif key in dic1 and key in dic2:
            merge_p_dic[key] = merge_previous_tuple(dic1[key], dic2[key])
        else:
            print("impossible")
    return merge_p_dic


def get_csv_files():
    files_name = []
    for file in os.listdir():
        if os.path.splitext(file)[1] == '.csv':
            files_name.append(file)
    return files_name


def csv2list(csv_file, window_length=3):
    step = 1 if window_length // 3 == 0 else window_length // 3
    windows_list = []
    index = 0
    df = pd.read_csv(csv_file)
    max_value = max(df['unit_gain'])
    while index + window_length + step - 1 <= df.shape[0]:
        temp = []
        for i in range(window_length):
            temp.append(format(float(df.iloc[index + i]['unit_gain']) / max_value, '.2f'))
        windows_list.append(tuple(temp))
        index += step
    return windows_list


def list2p_dic(windows_list):
    p_dic = {}
    length = len(windows_list) - 1
    for _index, _value in enumerate(windows_list):
        if _value not in p_dic:
            p_dic[_value] = {}
            if _index + 1 <= length:
                p_dic[_value] = {windows_list[_index + 1]: 1}
        else:
            if _index + 1 <= length:
                if windows_list[_index + 1] not in p_dic[_value]:
                    p_dic[_value] = {windows_list[_index + 1]: 1}
                else:
                    p_dic[_value][windows_list[_index + 1]] += 1
    return p_dic


def get_polymorphism_p_dic(csv_file, window_length_list):
    polymorphism_p_dic = {}
    for size in window_length_list:
        single_list = csv2list(csv_file, window_length=size)
        single_p_dic = list2p_dic(single_list)
        polymorphism_p_dic[str(size)] = single_p_dic
    return polymorphism_p_dic


# def try_fit(p_dic, test_csv):
#     df = pd.read_csv(test_csv)
#     index = 0
#     step = 1
#     while index + step <= df.shape[0]


def main():
    final_p_dic = {}
    csv_files = get_csv_files()
    for csv_file in csv_files:
        single_polymorphism_p_dic = get_polymorphism_p_dic(csv_file, [1, 2, 3])
        final_p_dic = merge_polymorphism_p_dic(final_p_dic, single_polymorphism_p_dic)
    for i in final_p_dic:
        print(i, final_p_dic[i])


if __name__ == '__main__':
    main()
# for _value in p_dic:
#     print(max(zip(p_dic[_value].values(), p_dic[_value].keys())))
