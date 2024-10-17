# -*- coding: utf-8 -*-
import pymongo
from pymongo import MongoClient
import pytz
from datetime import datetime, timedelta

class MongoDBHandler:
    def __init__(self, host, port, db_name):
        # 定义时区
        self.utc_tz = pytz.utc  # UTC 时区
        self.beijing_tz = pytz.timezone('Asia/Shanghai')  # 北京时区

        # 连接到 MongoDB 数据库
        self.client = MongoClient(f"mongodb://{host}:{port}")
        self.db = self.client[db_name]  # 选择数据库

    def get_device_info(self):
        # 从集合 'controls' 中获取设备信息
        collection = self.db.controls
        documents = collection.find()  # 查找所有文档

        # 定义用于存储设备信息、规则信息和参数信息的列表
        device_info = []
        rule_info = []
        param_info = []
        cron_ = ""  # 初始化 cron 表达式

        # 遍历集合中的每个文档
        for doc in documents:
            cron_ = doc.get("cron")  # 获取文档中的 cron 表达式
            # 过滤出 name 为 "环浔大模型" 的记录
            if doc.get("name") != "环浔大模型":
                continue  # 如果 name 不是 "环浔大模型"，跳过该记录

            # 提取设备的最小值和最大值
            for device in doc.get("devices", []):
                device_info.append({
                    "id": device["id"],  # 设备ID
                    "min": device["min"],  # 最小值
                    "max": device["max"]   # 最大值
                })

            # 提取每个设备的 USL、UCL、LCL、LSL 值
            for rule in doc.get("rules", []):
                rule_info.append({
                    "deviceId": rule["deviceId"],  # 设备ID
                    "USL": next((item["val"] for item in rule["typeList"] if item["name"] == "USL"), None),  # USL值
                    "UCL": next((item["val"] for item in rule["typeList"] if item["name"] == "UCL"), None),  # UCL值
                    "LCL": next((item["val"] for item in rule["typeList"] if item["name"] == "LCL"), None),  # LCL值
                    "LSL": next((item["val"] for item in rule["typeList"] if item["name"] == "LSL"), None)   # LSL值
                })

            # 提取每个参数的名称和值
            for param in doc.get("paramList", []):
                param_info.append({
                    "name": param["name"],  # 参数名称
                    "val": param["val"]     # 参数值
                })

        return device_info, rule_info, param_info, cron_  # 返回设备信息、规则信息、参数信息和 cron 表达式

    def get_devices(self):
        # 从集合 'configs' 中获取所有设备配置
        configs_collection = self.db.configs
        return list(configs_collection.find())  # 返回配置列表

    def get_last_rtd_data_DO(self, device_name_contains, extra_fields=None, num_to_display=10):
        # 根据设备名称关键字获取相关设备的实时数据
        configs_collection = self.db.configs
        devices = list(configs_collection.find({"name": {"$regex": device_name_contains}}))  # 根据名称正则表达式查找设备

        # 创建设备ID字典
        device_ids = {}
        for device in devices:
            device_ids[device['name']] = device['id']  # 将设备名称映射到设备ID

        output_str = []

        # 遍历设备ID字典，获取每个设备的最后一条实时数据
        for device_name, device_id in device_ids.items():
            collection_name = f"{device_id}_LOG"  # 实时数据集合的名称
            last_log_entry = self.db[collection_name].find_one(sort=[("_id", pymongo.DESCENDING)])  # 查找最新一条数据记录

            if last_log_entry:
                rtd_data = last_log_entry.get("rtd", [])  # 获取实时数据

                if len(rtd_data) < num_to_display:
                    # 如果最新一条记录的实时数据数量不足，获取倒数第二条记录的数据补足
                    second_last_log_entry = self.db[collection_name].find_one(sort=[("_id", pymongo.DESCENDING)], skip=1)
                    if second_last_log_entry:
                        second_last_rtd = second_last_log_entry.get("rtd", [])
                        remaining_count = num_to_display - len(rtd_data)
                        last_rtd = second_last_rtd[-remaining_count:] + rtd_data  # 补全数据
                    else:
                        last_rtd = rtd_data[-num_to_display:]  # 如果没有第二条记录，截取最新数据
                else:
                    last_rtd = rtd_data[-num_to_display:]  # 只保留指定数量的数据

                # 格式化并输出数据
                for data in last_rtd:
                    dataTime = data.get("dateTime")  # 获取数据时间
                    if dataTime and isinstance(dataTime, datetime):
                        dataTime_utc = dataTime.replace(tzinfo=self.utc_tz)  # 将时间设置为 UTC 时区
                        dataTime_beijing = dataTime_utc.astimezone(self.beijing_tz)  # 转换为北京时区
                        dataTime_str = dataTime_beijing.strftime("%Y-%m-%d %H:%M:%S")  # 格式化为字符串
                    else:
                        dataTime_str = "Unknown"  # 如果时间不可用，返回 "Unknown"

                    output = {
                        "Device ID": device_id,  # 设备ID
                        "dataTime": dataTime_str  # 数据时间
                    }
                    if extra_fields:
                        for field in extra_fields:
                            field_value = data.get(field)  # 获取额外字段的值
                            output[field] = field_value  # 将字段和值添加到输出
                    output_str.append(output)  # 添加到输出列表
            else:
                output_str.append({"message": f"No data found for device ID: {device_id}"})  # 如果没有数据，输出提示信息

        return output_str  # 返回输出字符串列表

    def get_last_rtd_data_FengJi(self, device_name_contains, extra_fields=None, num_to_display=10):
        # 根据设备名称关键字获取相关设备的实时数据
        configs_collection = self.db.configs
        devices = list(configs_collection.find({"name": {"$regex": device_name_contains}}))  # 根据名称正则表达式查找设备

        # 创建设备ID字典
        device_ids = {}
        for device in devices:
            device_ids[device['name']] = device['id']  # 将设备名称映射到设备ID

        output_str = []
        # 遍历设备ID字典，获取每个设备的最后一条实时数据
        for device_name, device_id in device_ids.items():
            collection_name = f"{device_id}_LOG"  # 实时数据集合的名称
            last_log_entry = self.db[collection_name].find_one(sort=[("_id", pymongo.DESCENDING)])  # 查找最新一条数据记录

            if last_log_entry:
                rtd_data = last_log_entry.get("rtd", [])  # 获取实时数据

                # 只保留指定数量的数据
                last_rtd = rtd_data[-num_to_display:] if len(rtd_data) >= num_to_display else rtd_data

                # 获取当前时间
                current_time = datetime.now(self.utc_tz)

                # 格式化并输出数据
                for data in last_rtd:
                    dataTime = data.get("dateTime")  # 获取数据时间
                    if dataTime and isinstance(dataTime, datetime):
                        dataTime_utc = dataTime.replace(tzinfo=self.utc_tz)  # 将时间设置为 UTC 时区
                        dataTime_beijing = dataTime_utc.astimezone(self.beijing_tz)  # 转换为北京时区
                        dataTime_str = dataTime_beijing.strftime("%Y-%m-%d %H:%M:%S")  # 格式化为字符串

                        # 判断时间差
                        extra_field_value = -1 if (current_time - dataTime_utc) > timedelta(minutes=5) else None
                    output = {
                        "Device ID": device_id,  # 设备ID
                        "dataTime": dataTime_str  # 数据时间
                    }
                    # 处理extra_fields
                    if extra_fields:
                        for field in extra_fields:
                            output[field] = extra_field_value if extra_field_value is not None else data.get(
                                field)  # 设置extra_fields的值

                    output_str.append(output)  # 添加到输出列表
            else:
                # 获取当前北京时间
                current_time_str = datetime.now(self.beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

                output = {
                    "Device ID": device_id,  # 设备ID
                    "dataTime": current_time_str  # 数据时间设为当前时间
                }
                if extra_fields:
                    for field in extra_fields:
                        output[field] = -1  # 将额外字段设为 None
                output_str.append(output)  # 添加到输出列表

        return output_str  # 返回输出字符串列表



    def ControlLog(self):
        # 使用固定的集合名 'ControlLog' 获取控制日志
        collection_name = "ControlLog"
        last_log_entry = self.db[collection_name].find_one(sort=[("_id", pymongo.DESCENDING)])  # 获取最新的一条日志记录
        if last_log_entry:
            # 获取最后一条记录的 rtdData 数据
            rtd_data = last_log_entry.get("rtdData", {})
            # 尝试获取 '环浔' 和 'number' 的值
            huan_xun_value = rtd_data.get("环浔", "智控算法")  # 如果不存在返回 '智控算法'
            number_value = rtd_data.get("number", 0)  # 如果不存在返回 0

            # 返回 '环浔' 和 'number' 的值
            return huan_xun_value, number_value
        else:
            return "智控算法", 0


    def close_connection(self):
        # 关闭 MongoDB 连接
        self.client.close()