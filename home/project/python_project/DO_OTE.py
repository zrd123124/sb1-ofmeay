# -*- coding: utf-8 -*-

def determine_adjustment(DO1_LCL, DO1_LSL, DO1_UCL, DO1_USL, DO2_LCL, DO2_LSL, DO2_UCL, DO2_USL,
                         DO1_实测, DO2_实测, OTE优化, control_, huan_xun_value):
    # 如果 DO1 或 DO2 的加权平均值小于或等于 LSL (下限设定值)，则返回增大调节量 5，保持当前 control_ 值
    if DO1_实测 < DO1_LCL or DO2_实测 < DO2_LCL:
        if DO1_实测 <= DO1_LSL or DO2_实测 <= DO2_LSL:
            return 5, control_
        else:
            return 3, control_
    # 如果 DO1 或 DO2 的加权平均值位于 UCL (上限控制界限) 和 USL 之间，则返回减小调节量 -3，保持当前 control_ 值
    elif DO1_实测 > DO1_UCL or DO2_实测 > DO2_UCL:
        if DO1_实测 >= DO1_USL or DO2_实测 >= DO2_USL:
            return -5, control_
        else:
            return -3, control_
    # 如果 DO1 的加权平均值位于 (LCL + UCL)/2 和 UCL 之间，且 DO2 的加权平均值位于 (2*LCL + UCL)/3 和 UCL 之间
    elif (DO1_LCL + DO1_UCL) / 2 <= DO1_实测 <= DO1_UCL and \
            (2 * DO2_LCL + DO2_UCL) / 3 <= DO2_实测 <= DO2_UCL:
        # 如果 OTE优化为 0 并且 huan_xun_value 为 '智控算法'，则更新 control_ 为 "OTE优化"，返回减小调节量 -2
        if OTE优化 == 0 and huan_xun_value == '智控算法':
            control_ = "OTE优化"
            return -2, control_
        # 如果 huan_xun_value 为 'OTE优化'，则更新 control_ 为 "OTE优化"，返回减小调节量 -2
        elif huan_xun_value == 'OTE优化':
            control_ = "OTE优化"
            return -2, control_
    # 如果以上条件都不满足，则默认返回不增不减的调节量 0，保持当前 control_ 值
    return 0, control_


def determine_adjustment_Dochange(DO1_LCL, DO1_LSL, DO1_UCL, DO1_USL, DO2_LCL, DO2_LSL, DO2_UCL, DO2_USL,
                                  DO1_实测, DO2_实测, OTE优化, control_, huan_xun_value, 容忍度):
    if DO1_实测 < DO1_LCL and DO2_实测 > DO2_UCL:
        new_DO1_LCL = DO1_LCL - 容忍度
        if DO1_实测 >= new_DO1_LCL:
            return 0, control_
        else:
            return 5, control_
    # 如果 DO1 或 DO2 的加权平均值小于或等于 LSL (下限设定值)，则返回增大调节量 5，保持当前 control_ 值
    elif DO1_实测 < DO1_LCL or DO2_实测 < DO2_LCL:
        if DO1_实测 <= DO1_LSL or DO2_实测 <= DO2_LSL:
            return 5, control_
        else:
            return 3, control_
    # 如果 DO1 或 DO2 的加权平均值位于 UCL (上限控制界限) 和 USL 之间，则返回减小调节量 -3，保持当前 control_ 值
    elif DO1_实测 > DO1_UCL or DO2_实测 > DO2_UCL:
        if DO1_实测 >= DO1_USL or DO2_实测 >= DO2_USL:
            return -5, control_
        else:
            return -3, control_
    # 特殊情况处理：
    # 如果 DO1 的加权平均值位于 (LCL + UCL)/2 和 UCL 之间，且 DO2 的加权平均值位于 (2*LCL + UCL)/3 和 UCL 之间
    elif (DO1_LCL + DO1_UCL) / 2 <= DO1_实测 <= DO1_UCL and \
            (2 * DO2_LCL + DO2_UCL) / 3 <= DO2_实测 <= DO2_UCL:
        # 如果 OTE优化为 0 并且 huan_xun_value 为 '智控算法'，则更新 control_ 为 "OTE优化"，返回减小调节量 -2
        if OTE优化 == 0 and huan_xun_value == '智控算法':
            control_ = "OTE优化"
            return -2, control_
        # 如果 huan_xun_value 为 'OTE优化'，则更新 control_ 为 "OTE优化"，返回减小调节量 -2
        elif huan_xun_value == 'OTE优化':
            control_ = "OTE优化"
            return -2, control_
    # 如果以上条件都不满足，则默认返回不增不减的调节量 0，保持当前 control_ 值
    return 0, control_