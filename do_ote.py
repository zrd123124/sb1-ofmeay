# -*- coding: utf-8 -*-

def determine_adjustment(DO1_LCL, DO1_LSL, DO1_UCL, DO1_USL, DO2_LCL, DO2_LSL, DO2_UCL, DO2_USL,
                         DO1_actual, DO2_actual, OTE_optimization, control_, huan_xun_value):
    if DO1_actual < DO1_LCL or DO2_actual < DO2_LCL:
        if DO1_actual <= DO1_LSL or DO2_actual <= DO2_LSL:
            return 5, control_
        else:
            return 3, control_
    elif DO1_actual > DO1_UCL or DO2_actual > DO2_UCL:
        if DO1_actual >= DO1_USL or DO2_actual >= DO2_USL:
            return -5, control_
        else:
            return -3, control_
    elif (DO1_LCL + DO1_UCL) / 2 <= DO1_actual <= DO1_UCL and \
            (2 * DO2_LCL + DO2_UCL) / 3 <= DO2_actual <= DO2_UCL:
        if OTE_optimization == 0 and huan_xun_value == '智控算法':
            control_ = "OTE优化"
            return -2, control_
        elif huan_xun_value == 'OTE优化':
            control_ = "OTE优化"
            return -2, control_
    return 0, control_


def determine_adjustment_Dochange(DO1_LCL, DO1_LSL, DO1_UCL, DO1_USL, DO2_LCL, DO2_LSL, DO2_UCL, DO2_USL,
                                  DO1_actual, DO2_actual, OTE_optimization, control_, huan_xun_value, tolerance):
    if DO1_actual < DO1_LCL and DO2_actual > DO2_UCL:
        new_DO1_LCL = DO1_LCL - tolerance
        if DO1_actual >= new_DO1_LCL:
            return 0, control_
        else:
            return 5, control_
    elif DO1_actual < DO1_LCL or DO2_actual < DO2_LCL:
        if DO1_actual <= DO1_LSL or DO2_actual <= DO2_LSL:
            return 5, control_
        else:
            return 3, control_
    elif DO1_actual > DO1_UCL or DO2_actual > DO2_UCL:
        if DO1_actual >= DO1_USL or DO2_actual >= DO2_USL:
            return -5, control_
        else:
            return -3, control_
    elif (DO1_LCL + DO1_UCL) / 2 <= DO1_actual <= DO1_UCL and \
            (2 * DO2_LCL + DO2_UCL) / 3 <= DO2_actual <= DO2_UCL:
        if OTE_optimization == 0 and huan_xun_value == '智控算法':
            control_ = "OTE优化"
            return -2, control_
        elif huan_xun_value == 'OTE优化':
            control_ = "OTE优化"
            return -2, control_
    return 0, control_