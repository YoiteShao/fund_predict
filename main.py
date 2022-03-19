import pandas as pd
import math
import os
import pickle
import matplotlib.ticker as ticker
from matplotlib import pyplot as plt


# p_dic = {previous_tuple:{next_tuple:Int, ...}, ...}
# polymorphic_p_dic = {size:p_dic, ...}
def softmax_p_dic_value(dic):
    """
    Regularize every next_tuple count to probability
    :param dic:p_dic, key=previous_tuple, value=next_tuple count
    :return:Regularized p_dic
    """
    for _tuple in dic:
        _sum = 0
        for _tuple_behind in dic[_tuple]:
            _sum += math.exp(dic[_tuple][_tuple_behind])
        for _tuple_behind in dic[_tuple]:
            dic[_tuple][_tuple_behind] = math.exp(dic[_tuple][_tuple_behind]) / _sum
    return dic


def merge_next_tuple(dic1, dic2):
    """
    Merge next_tuple probability if is same next_tuple
    :param dic1: be merged next_tuple dict
    :param dic2: be merged next_tuple dict
    :return: merged next_tuple dict
    """
    grouping_dic = dict()
    for key in dic1.keys() | dic2.keys():
        grouping_dic[key] = sum([dic.get(key, 0) for dic in (dic1, dic2)])
    return grouping_dic


def merge_previous_tuple(dic1, dic2):
    """
    Merge previous_tuple if same previous_tuple
    :param dic1: be merged previous_tuple dict
    :param dic2: be merged previous_tuple dict
    :return: merged previous_tuple dict
    """
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


def merge_sizes_p_dic(dic1, dic2):
    """
    Merge all the windows_length p_dic
    :param dic1: be merged p_dic
    :param dic2: be merged p_dic
    :return: merged sizes p_dic
    """
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
    """
    Get all .csv files
    :return: csv files list
    """
    files_name = []
    for file in os.listdir():
        if os.path.splitext(file)[1] == '.csv':
            files_name.append(file)
    return files_name


def csv2list(csv_file, window_length, accuracy):
    """
    transfer csv to timing windows list
    :param accuracy: Effective accuracy
    :param csv_file: csv file
    :param window_length: window length
    :return: timing windows list
    """
    step = 1 if window_length // 3 == 0 else window_length // 3
    windows_list = []
    index = 0
    df = pd.read_csv(csv_file)
    max_value = max(df['unit_gain'])
    df['unit_gain'] = round(df['unit_gain'] / max_value, accuracy)
    while index + window_length + step - 1 <= df.shape[0]:
        temp = []
        for i in range(window_length):
            temp.append(df.iloc[index + i]['unit_gain'])
        windows_list.append(tuple(temp))
        index += step
    return windows_list


def list2p_dic(windows_list):
    """
    transfer windows list to
    :param windows_list
    :return: the probability of every window in next order dict
    """
    p_dic = {}
    length = len(windows_list) - 1
    for _index, _value in enumerate(windows_list):
        if _value not in p_dic:
            p_dic[_value] = {}
            if _index + 1 <= length:
                p_dic[_value][windows_list[_index + 1]] = 1
        else:
            if _index + 1 <= length:
                if windows_list[_index + 1] not in p_dic[_value]:
                    p_dic[_value][windows_list[_index + 1]] = 1
                else:
                    p_dic[_value][windows_list[_index + 1]] += 1
    return p_dic


def get_sizes_p_dic(csv_file, window_length_list, accuracy):
    """
    Get all size p_dic from window length list with target csv file
    :param accuracy: Effective accuracy
    :param csv_file: csv file
    :param window_length_list: window length list
    :return: sizes p_dic
    """
    sizes_p_dic = {}
    for size in window_length_list:
        single_list = csv2list(csv_file, size, accuracy)
        single_p_dic = list2p_dic(single_list)
        sizes_p_dic[size] = single_p_dic
    return sizes_p_dic


def try_fit(p_dic, abnormal_p, test_csv, tested_windows_length_list, accuracy):
    """
    detect all the low probability point that is abnormal in test csv
    :param accuracy: Effective accuracy
    :param abnormal_p: abnormal probability should be
    :param p_dic:sizes p_dic
    :param test_csv:tested csv file
    :param tested_windows_length_list:need to be detected windows size
    :return:
    """
    abnormal_point = {}
    for i, size in enumerate(tested_windows_length_list):
        print('\rTry to fit：{}{}%'.format('▉*' * (i // len(tested_windows_length_list)), (i * 10)), end='')
        if size not in p_dic:
            continue
        abnormal_point[size] = []

        df = pd.read_csv(test_csv)
        step = 1 if size // 3 == 0 else size // 3
        index = 0
        max_value = max(df['unit_gain'])
        while index + size + step < df.shape[0]:
            check_window = tuple(round(df.iloc[index:index + size]['unit_gain'] / max_value, accuracy))
            if check_window not in p_dic[size]:
                abnormal_point[size].extend([_ for _ in range(index, index + size)])
            else:
                if index + size + step < df.shape[0]:
                    check_window_next = tuple(
                        round(df.iloc[index + step:index + size + step]['unit_gain'] / max_value, accuracy))
                    tested_p = p_dic[size][check_window].get(check_window_next, 0)
                    if tested_p <= abnormal_p:
                        abnormal_point[size].extend([_ for _ in range(index + step, index + size + step)])
            index += step

    plt.plot(df['date'], df['unit_gain'], color='red', alpha=0.7)
    for size in tested_windows_length_list:
        x = [df.iloc[_]['date'] for _ in abnormal_point[size]]
        y = [df.iloc[_]['unit_gain'] for _ in abnormal_point[size]]
        plt.scatter(x, y, marker='o', s=10, clip_on=False, label='range ' + str(size) + ' Abnormal point')
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(90))
    plt.xticks(rotation=60)
    plt.ylabel("Value")
    plt.legend(loc='lower right')
    plt.show()


def main():
    final_p_dic = {}
    csv_files = get_csv_files()
    # csv_files = ['D:\\Treasure\\PythonCode\\fund_code\\_predict_test_000209.csv']
    accuracy = 2
    for i, csv_file in enumerate(csv_files):
        single_size_p_dic = get_sizes_p_dic(csv_file, [1, 2, 3], accuracy)
        final_p_dic = merge_sizes_p_dic(final_p_dic, single_size_p_dic)
        print('\rGet sizes dict：{}{}%'.format('▉*' * (i // len(csv_files)), (i * 10)), end='')
    try_fit(final_p_dic, 0.8, "D:\\Treasure\\PythonCode\\fund_code\\_predict_test_000209.csv", [1,2], accuracy)
    # for size in final_p_dic:
    #     for pre_tuple in final_p_dic[size]:
    #         print(final_p_dic[size][pre_tuple])


if __name__ == '__main__':
    main()
# for _value in p_dic:
#     print(max(zip(p_dic[_value].values(), p_dic[_value].keys())))
