#! /bin/python3

def image_policy_disk_excludes(policy_name):
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

    policy_name = policy_name.lower()
    data = subprocess.check_output(rf"/usr/openv/netbackup/bin/admincmd/bppllist {policy_name}", shell=True, stderr=subprocess.DEVNULL).decode()

    #debug
    # print(f"policy name {policy_name} \n sql in policy name: {'sql' in policy_name} \n image in policy name {'image' in policy_name}")
    # print(f"'SSMARG drive_selection 2' in data: {'SSMARG drive_selection 2' in data}")
    # print(f"'SSMARG drive_selection 0' in data: {'SSMARG drive_selection 0' in data}")

    if "image" in policy_name and not "sql" in policy_name and "SSMARG drive_selection 0" in data:  # checking image policy
        return True

    return True if "image" in policy_name and "sql" in policy_name and "SSMARG drive_selection 2" in data else False  # checking SQL policy


# testing

import subprocess, sys, datetime, openpyxl, shutil

policies = subprocess.check_output(r"/usr/openv/netbackup/bin/admincmd/bppllist", shell=True).decode().split("\n")
errors = []
success = []

for policy in policies:
    if "image" in policy or "image" in policy and "sql" in policy:
        try:
            result = image_policy_disk_excludes(policy)
            if not result:
                errors.append(policy)
                continue
            success.append(policy)
        except Exception as e:
            print(f"{policy} does not exist in the configuration database (230)") if "230" in str(e) else sys.exit(f" error is {e}")

print("SUCCESS POLICIES:")
for item in success:
    print(item)

print("FAILED POLICIES:")
if errors:
    for item in errors:
        print(item)
