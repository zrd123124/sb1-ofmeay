# -*- coding: utf-8 -*-
import pymongo
from pymongo import MongoClient
import pytz
from datetime import datetime, timedelta

class MongoDBHandler:
    def __init__(self, host, port, db_name):
        self.utc_tz = pytz.utc
        self.beijing_tz = pytz.timezone('Asia/Shanghai')

        self.client = MongoClient(f"mongodb://{host}:{port}")
        self.db = self.client[db_name]

    def get_device_info(self):
        collection = self.db.controls
        documents = collection.find()

        device_info = []
        rule_info = []
        param_info = []
        cron_ = ""

        for doc in documents:
            cron_ = doc.get("cron")
            if doc.get("name") != "环浔大模型":
                continue

            for device in doc.get("devices", []):
                device_info.append({
                    "id": device["id"],
                    "min": device["min"],
                    "max": device["max"]
                })

            for rule in doc.get("rules", []):
                rule_info.append({
                    "deviceId": rule["deviceId"],
                    "USL": next((item["val"] for item in rule["typeList"] if item["name"] == "USL"), None),
                    "UCL": next((item["val"] for item in rule["typeList"] if item["name"] == "UCL"), None),
                    "LCL": next((item["val"] for item in rule["typeList"] if item["name"] == "LCL"), None),
                    "LSL": next((item["val"] for item in rule["typeList"] if item["name"] == "LSL"), None)
                })

            for param in doc.get("paramList", []):
                param_info.append({
                    "name": param["name"],
                    "val": param["val"]
                })

        return device_info, rule_info, param_info, cron_

    def get_devices(self):
        configs_collection = self.db.configs
        return list(configs_collection.find())

    def get_last_rtd_data_DO(self, device_name_contains, extra_fields=None, num_to_display=10):
        configs_collection = self.db.configs
        devices = list(configs_collection.find({"name": {"$regex": device_name_contains}}))

        device_ids = {}
        for device in devices:
            device_ids[device['name']] = device['id']

        output_str = []

        for device_name, device_id in device_ids.items():
            collection_name = f"{device_id}_LOG"
            last_log_entry = self.db[collection_name].find_one(sort=[("_id", pymongo.DESCENDING)])

            if last_log_entry:
                rtd_data = last_log_entry.get("rtd", [])

                if len(rtd_data) < num_to_display:
                    second_last_log_entry = self.db[collection_name].find_one(sort=[("_id", pymongo.DESCENDING)], skip=1)
                    if second_last_log_entry:
                        second_last_rtd = second_last_log_entry.get("rtd", [])
                        remaining_count = num_to_display - len(rtd_data)
                        last_rtd = second_last_rtd[-remaining_count:] + rtd_data
                    else:
                        last_rtd = rtd_data[-num_to_display:]
                else:
                    last_rtd = rtd_data[-num_to_display:]

                for data in last_rtd:
                    dataTime = data.get("dateTime")
                    if dataTime and isinstance(dataTime, datetime):
                        dataTime_utc = dataTime.replace(tzinfo=self.utc_tz)
                        dataTime_beijing = dataTime_utc.astimezone(self.beijing_tz)
                        dataTime_str = dataTime_beijing.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        dataTime_str = "Unknown"

                    output = {
                        "Device ID": device_id,
                        "dataTime": dataTime_str
                    }
                    if extra_fields:
                        for field in extra_fields:
                            field_value = data.get(field)
                            output[field] = field_value
                    output_str.append(output)
            else:
                output_str.append({"message": f"No data found for device ID: {device_id}"})

        return output_str

    def get_last_rtd_data_fan(self, device_name_contains, extra_fields=None, num_to_display=10):
        configs_collection = self.db.configs
        devices = list(configs_collection.find({"name": {"$regex": device_name_contains}}))

        device_ids = {}
        for device in devices:
            device_ids[device['name']] = device['id']

        output_str = []
        for device_name, device_id in device_ids.items():
            collection_name = f"{device_id}_LOG"
            last_log_entry = self.db[collection_name].find_one(sort=[("_id", pymongo.DESCENDING)])

            if last_log_entry:
                rtd_data = last_log_entry.get("rtd", [])

                last_rtd = rtd_data[-num_to_display:] if len(rtd_data) >= num_to_display else rtd_data

                current_time = datetime.now(self.utc_tz)

                for data in last_rtd:
                    dataTime = data.get("dateTime")
                    if dataTime and isinstance(dataTime, datetime):dataTime_utc = dataTime.replace(tzinfo=self.utc_tz)
                        dataTime_beijing = dataTime_utc.astimezone(self.beijing_tz)
                        dataTime_str = dataTime_beijing.strftime("%Y-%m-%d %H:%M:%S")

                        extra_field_value = -1 if (current_time - dataTime_utc) > timedelta(minutes=5) else None
                    output = {
                        "Device ID": device_id,
                        "dataTime": dataTime_str
                    }
                    if extra_fields:
                        for field in extra_fields:
                            output[field] = extra_field_value if extra_field_value is not None else data.get(
                                field)

                    output_str.append(output)
            else:
                current_time_str = datetime.now(self.beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

                output = {
                    "Device ID": device_id,
                    "dataTime": current_time_str
                }
                if extra_fields:
                    for field in extra_fields:
                        output[field] = -1
                output_str.append(output)

        return output_str

    def ControlLog(self):
        collection_name = "ControlLog"
        last_log_entry = self.db[collection_name].find_one(sort=[("_id", pymongo.DESCENDING)])
        if last_log_entry:
            rtd_data = last_log_entry.get("rtdData", {})
            huan_xun_value = rtd_data.get("环浔", "智控算法")
            number_value = rtd_data.get("number", 0)

            return huan_xun_value, number_value
        else:
            return "智控算法", 0

    def close_connection(self):
        self.client.close()