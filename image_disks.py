#! /bin/python3

def image_policy_disk_excludes(data):
    """
    :param policy_name: name of the policy we are going to check
    :type policy_name: str
    :return: True if settings are correct, else False
    :rtype: bool
    Logic: if policy name contains "image" and "sql" - it should have drive_selection 2 value in settings file (bppllist policy_name)
    if policy names contains "image" but not "sql" - drive_selection 0 should be in settings
    """

    import subprocess, os, sys, platform

    # precheck if we're running on Linux

    if platform.system() != "Linux":
        sys.exit(f"OS was detected as {platform.system()}, should be 'Linux'")
    try:
        policy_name = re.findall(r"^CLASS\s([a-zA-Z0-9-_.]*)\s", data)[0]
    except:
        print(data)
    if "image" in policy_name or "image" in policy_name and "sql" in policy_name:

        # debug
        # print(f"policy name {policy_name} \n sql in policy name: {'sql' in policy_name} \n image in policy name {'image' in policy_name}")
        # print(f"'SSMARG drive_selection 2' in data: {'SSMARG drive_selection 2' in data}")
        # print(f"'SSMARG drive_selection 0' in data: {'SSMARG drive_selection 0' in data}")

        if "image" in policy_name and not "sql" in policy_name and "SSMARG drive_selection 0" in data:  # checking image policy
            return True, policy_name, "OK"

        return (True, policy_name,
                "OK") if "image" in policy_name and "sql" in policy_name and "SSMARG drive_selection 2" in data else (
        False, policy_name, "Image backup disk exclusion check failed")  # checking SQL policy

    else:
        return True, policy_name, "OK"


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
    if policy_type == "40":  # VMWare
        if "Full" in schedule_name and schedule_code != "0":
            return False
        elif "Dif" in schedule_name and schedule_code != "1":
            return False
    if any(policy_type == i for i in
           ["13", "16", "29", "25", "0", "4"]):  # MS-Windows & Exchange & Flashbackup & LotusNotes & Oracle & Standard
        if "Full" in schedule_name and schedule_code != "0":
            return False
        elif "Cum" in schedule_name and schedule_code != "4":
            return False
        elif "Dif" in schedule_name and schedule_code != "1":
            return False
    if policy_type == "15" and "intel" in policy_name:  # MSSQL Intelligent
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
    retentions = \
        {
            "2y": "12",
            "5y": "13",
            "10y": "16",
            "30m": "17",
            "8m": "4",
            "6w": "10",
            "2w": "1"
        }
    # policy_types = \
    #     {
    #     "13": "MS-Windows",
    #     "0": "Standard",
    #     "15": "MS-SQL",
    #     "16": "Exchange",
    #     "40": "VMware",
    #     "4": "Oracle",
    #     "29": "Flashbackup",
    #     "30": "Vault",
    #     "25": "LotusNotes"
    #     }
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
            # print(policy_type)
        if re.match("^RES", line):
            policy_default_slp = "".join([retentions[key] for key in retentions.keys() if key in line.lower()])
            # print(policy_default_slp)
        if re.match("^SCHED\\s", line):
            current_schedule = line.split()[1]
            current_schedule_code = line.split()[2]
            if not check_policy_schedules(policy_type, policy_name, current_schedule, current_schedule_code):
                #                print(rf"Check {current_schedule} of {policy_name}")
                return (False, f"schedule: {current_schedule} policy: {policy_name}", "Schedule check failed")
            # print(current_schedule)
        if re.match("^SCHEDRES\\s", line):
            current_schedule_retention_from_name = "".join(
                [retentions[key] for key in retentions.keys() if key in current_schedule.lower()])
            if "NULL" not in line.split()[1]:
                current_schedule_retention = "".join(
                    [retentions[key] for key in retentions.keys() if key in line.lower()])
                if current_schedule_retention != current_schedule_retention_from_name:
                    #                    policies_to_check.append(f"{policy_name} retention check failed")
                    return (False, f"schedule: {current_schedule} policy: {policy_name}", "Retention check failed")
            else:
                if policy_default_slp != current_schedule_retention_from_name and "App" not in current_schedule:
                    #                     print(rf"Check {current_schedule} of {policy_name}. Wrong schedule name.")
                    return (False, f"schedule: {current_schedule} policy: {policy_name}", "Schedule name check failed")
    return (True, policy_name, "OK")


# testing

import subprocess, sys, datetime, shutil, re

# import openpyxl

master_servers = ["dk-prod-nbumas04.prod.fujitsu.dk", "dk-prod-nbumas01.prod.fujitsu.dk",
                  "dk-prod-nbumasprisme.prod.fujitsu.dk"]

errors = dict()

for server in master_servers:
    policy_names_dict = dict()
    policies = subprocess.check_output(rf"/usr/bin/ssh root@{server} /usr/openv/netbackup/bin/admincmd/bppllist",
                                       shell=True).decode().split("\n")
    policy_names_dict[server] = policies
    print(policy_names_dict)
    for policy in policy_names_dict[server]:
        print(policy)
        # if policy == "":
        #     continue
        try:
            policy_data = subprocess.check_output(
                rf"/usr/bin/ssh root@{server} /usr/openv/netbackup/bin/admincmd/bppllist {policy}", shell=True).decode()
        except Exception as e:
            print(f"{policy} does not exist in the configuration database (230)") if "230" in str(e) else sys.exit(
                f" error is {e}")
            continue
        try:
            policy_name = re.findall(r"^CLASS\s([a-zA-Z0-9-_.]*)\s", policy_data)[0]
            result = [image_policy_disk_excludes(policy_data), check_policy_retention(policy_data)]
        except:
            print("")
        if policy_name in policy_names_dict.values():
            print(
                f"WARNING, DUPLICATE POLICY NAME FOUND: {policy_name} CONSIDER RENAMING ONE OF THE POLICIES WITH THE SAME NAME")
        if not all(result):
            errors.setdefault(policy_name, [r for r in result if not r[0]])

# policies = subprocess.check_output(r"/usr/openv/netbackup/bin/admincmd/bppllist", shell=True).decode().split("\n")

print(errors)
