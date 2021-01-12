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
            return dict.get(key)

def iterate_types(string, dict):
    for key in dict.keys():
        if string.lower() in key:
            return dict.get(key)

def check_policy_schedules(policy_type, policy_name, schedule_name, schedule_code):
    if "40" in policy_type:                                                         #VMWare
        if "Full" in schedule_name and schedule_code != "0":
            return False
        if "Dif" in schedule_name and schedule_code != "1":
            return False
    if "13" in policy_type \
            or policy_type in "0" \
            or "16" in policy_type \
            or policy_type in "4" \
            or "29" in policy_type \
            or "25" in policy_type:                                                  #MS-Windows & Standard  & Exchange & Oracle & Flashbackup & Lotus
        if "Full" in schedule_name and schedule_code != "0":
            return False
        if "Cum" in schedule_name and schedule_code != "4":
            return False
        if "Dif" in schedule_name and schedule_code != "1":
            return False
    if "15" in policy_type and "intel" in policy_name:                              #MSSQL Intelligent
        if "Full" in schedule_name and schedule_code != "0":
            return False
        if "Dif" in schedule_name and schedule_code != "1":
            return False
        if "log" in schedule_name and schedule_code != "5":
            return False

    return True


def check_policy_retention(policy_name):
    policy_info = subprocess.check_output(rf"/usr/openv/netbackup/bin/admincmd/bppllist {policy_name}", shell=True, stderr=subprocess.DEVNULL).decode()
    policy_type = ""
    policy_default_slp = ""
    current_schedule = ""
    current_schedule_code = ""
    for line in policy_info.splitlines():
        if re.match("^INFO", line):
            policy_type = line.split(" ")[1]
            print(policy_type)
        if re.match("^RES", line):
           policy_default_slp = iterate_dict(line, retentions)
           print(policy_default_slp)
        if re.match("^SCHED\\s", line):
            current_schedule = line.split(" ")[1]
            current_schedule_code = line.split(" ")[2]
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
                if policy_default_slp != current_schedule_retention_from_name:
                    print(rf"Check {current_schedule} of {policy_name}. Wrong schedule name")



# check_policy_retention("ccdk_bal_image")
# check_policy_retention("ccdk-fil-1")
# check_policy_retention("ccdk-sql-time")
check_policy_retention("ccdk-sql-intelligent-cold")
print(policies_to_check)

