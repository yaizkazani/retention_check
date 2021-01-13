#! /bin/python3

import subprocess, os, sys, platform, re

retentions = {"2y": "12",
              "5y": "13",
              "10y": "16",
              "30m": "17",
              "8m": "4",
              "6w": "10",
              "2w": "1"}

policy_types = {
    "13": "MS-Windows",
    "0": "Standard",
    "15": "MS-SQL",
    "16": "Exchange",
    "40": "VMware",
    "4": "Oracle",
    "29": "Flashbackup",
    "30": "Vault",
    "25": "LotusNotes"
}

temp = dict()

for key in policy_types.keys():
    temp.setdefault(policy_types[key], key)

# allSLPs = subprocess.check_output(rf"/usr/openv/netbackup/bin/admincmd/nbstl -L", shell=True, stderr=subprocess.DEVNULL).decode()
#
# slpName = ""
# slpName = ""
# slpRetention = ""
# slpToCheck = []
# for line in allSLPs.splitlines():
#     if re.match("^\\s+Name", line):
#         slpName = line[38:]
#         for key in retentions.keys():
#             if key in slpName.lower():
#                 slpRetention = retentions.get(key)
#     if re.match("^\\s+Retention Level", line):
#         if (slpRetention not in line):
#             slpToCheck.append(slpName)
# print(set(slpToCheck))

policies_to_check = []


def iterate_dict(string, dict):
    for key in dict.keys():
        if key in string.lower():
            return dict[key]


def check_policy_schedules(policy_type, policy_name, schedule_name, schedule_code):
    """
    Checks if policy schedule name corresponds to it's exact purpose.
    :param policy_type: policy type code represented in policy_types dict
    :param policy_name:
    :param schedule_name:
    :param schedule_code: schedule code from bppllist output
    :return:
    """
    if not any(name in schedule_name for name in ["Full", "Cum", "Dif", "log", "App"]):
        print(rf"Check {schedule_name} of {policy_name}. Wrong schedule name")
    if policy_type == "40":                                                                         # VMWare
        if "Full" in schedule_name and schedule_code != "0":
            return False
        elif "Dif" in schedule_name and schedule_code != "1":
            return False
    if any(policy_type == i for i in ["13", "16", "29", "25", "0", "4"]):            #MS-Windows & Exchange & Flashbackup & LotusNotes & Oracle & Standard
        if "Full" in schedule_name and schedule_code != "0":
            return False
        elif "Cum" in schedule_name and schedule_code != "4":
            return False
        elif "Dif" in schedule_name and schedule_code != "1":
            return False
    if policy_type == "15" and "intel" in policy_name:                                              # MSSQL Intelligent
        if "Full" in schedule_name and schedule_code != "0":
            return False
        elif "Dif" in schedule_name and schedule_code != "1":
            return False
        elif "log" in schedule_name and schedule_code != "5":
            return False

    return True


def check_policy_retention(policy_info):
    """
    Checks if policy schedule names corresponds it's exact retention.
    :param policy_info: policy information from bppllist output
    :return:
    """
    policy_name = ""
    policy_type = ""
    policy_default_slp = ""
    current_schedule = ""
    current_schedule_code = ""
    for line in policy_info.splitlines():
        if re.match("^CLASS", line):
            policy_name = line.split()[1]
        if re.match("^INFO", line):
            policy_type = line.split()[1]
            print(policy_type)
        if re.match("^RES", line):
            policy_default_slp = iterate_dict(line, retentions)
            print(policy_default_slp)
        if re.match("^SCHED\\s", line):
            current_schedule = line.split()[1]
            current_schedule_code = line.split()[2]
            if not check_policy_schedules(policy_type, policy_name, current_schedule, current_schedule_code):
                print(rf"Check {current_schedule} of {policy_name}")
            print(current_schedule)
        if re.match("^SCHEDRES\\s", line):
            current_schedule_retention_from_name = iterate_dict(current_schedule, retentions)
            if "NULL" not in line.split()[1]:
                current_schedule_retention = iterate_dict(line, retentions)
                if current_schedule_retention != current_schedule_retention_from_name:
                    policies_to_check.append(policy_name)
            else:
                if policy_default_slp != current_schedule_retention_from_name and "App" not in current_schedule:
                    print(rf"Check {current_schedule} of {policy_name}. Wrong schedule name.")


# check_policy_retention("ccdk_bal_image")
# check_policy_retention("ccdk-fil-1")
# check_policy_retention("ccdk-sql-time")
check_policy_retention(subprocess.check_output(rf"/usr/openv/netbackup/bin/admincmd/bppllist ccdk-ora-day", shell=True,
                                               stderr=subprocess.DEVNULL).decode())
print(policies_to_check)
