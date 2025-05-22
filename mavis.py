#!/usr/bin/env python3
import sys
import re
from typing import Optional

# MAVIS attribute indices (from Mavis.pm)
AV_A_TYPE = 0
AV_A_MEMBEROF = 1
AV_A_SSHKEYHASH = 2
AV_A_TIMESTAMP = 3
AV_A_USER = 4
AV_A_DN = 5
AV_A_RESULT = 6
AV_A_PATH = 7
AV_A_PASSWORD = 8
AV_A_UID = 9
AV_A_GID = 10
AV_A_LIMIT = 11
AV_A_SSHKEY = 12
AV_A_TRAFFICSHAPING = 13
AV_A_IPADDR = 14
AV_A_QUOTA_LIMIT = 15
AV_A_QUOTA_PATH = 16
AV_A_COMMENT = 17
AV_A_SSHKEYID = 18
AV_A_HOME = 19
AV_A_ROOT = 20
AV_A_SERIAL = 21
AV_A_FTP_ANONYMOUS = 22
AV_A_EMAIL = 23
AV_A_GIDS = 24
AV_A_SERVERIP = 25
AV_A_ARGS = 26
AV_A_REALM = 27
AV_A_RARGS = 28
AV_A_ANON_INCOMING = 29
AV_A_VHOST = 30
AV_A_UMASK = 31
AV_A_USER_RESPONSE = 32
AV_A_VERDICT = 33
AV_A_CLASS = 34
AV_A_PASSWORD_EXPIRY = 35
AV_A_DBPASSWORD = 36
AV_A_IDENTITY_SOURCE = 37
AV_A_CUSTOM_0 = 38
AV_A_CUSTOM_1 = 39
AV_A_CUSTOM_2 = 40
AV_A_CUSTOM_3 = 41
AV_A_CALLER_CAP = 42
AV_A_CERTDATA = 43
AV_A_CERTSUBJ = 44
AV_A_DBCERTSUBJ = 45
AV_A_TACCLIENT = 46
AV_A_TACMEMBER = 47
AV_A_TACPROFILE = 48
AV_A_TACTYPE = 49
AV_A_PASSWORD_NEW = 50
AV_A_CHALLENGE = 51
AV_A_PASSWORD_ONESHOT = 52
AV_A_PASSWORD_MUSTCHANGE = 53
AV_A_SHELL = 54
AV_A_CURRENT_MODULE = 55
AV_A_ARRAYSIZE = 56

# MAVIS values
AV_V_TYPE_TACPLUS = "TACPLUS"
AV_V_TACTYPE_HOST = "HOST"
AV_V_TACTYPE_DACL = "DACL"
AV_V_TACTYPE_INFO = "INFO"
AV_V_TACTYPE_AUTH = "AUTH"
AV_V_TACTYPE_CHPW = "CHPW"
AV_V_RESULT_OK = "ACK"
AV_V_RESULT_FAIL = "NAK"
AV_V_RESULT_ERROR = "ERR"
MAVIS_FINAL = 0
MAVIS_DEFERRED = 1
MAVIS_DOWN = 16

def parse_av_pairs(input_block):
    V: list[Optional[str]] = [None] * (AV_A_ARRAYSIZE + 1)
    for line in input_block.strip().split('\n'):
        m = re.match(r'^(\d+)\s(.*)$', line)
        if m:
            idx, val = int(m.group(1)), m.group(2)
            if idx <= AV_A_ARRAYSIZE:
                V[idx] = val
    return V

def output_av_pairs(V, result):
    out = ""
    for i, v in enumerate(V):
        if v is not None:
            v = v.replace('\n', '\r').replace('\0', '')
            out += f"{i} {v}\n"
    out += f"={result}\n"
    print(out, end='')

def main():
    buffer = ""
    for line in sys.stdin:
        if line == "=\n":
            V = parse_av_pairs(buffer)
            result = MAVIS_DEFERRED

            # Type check
            if V[AV_A_TYPE] and V[AV_A_TYPE] != AV_V_TYPE_TACPLUS:
                result = MAVIS_DOWN
                output_av_pairs(V, result)
                buffer = ""
                continue

            # User must be set
            if not V[AV_A_USER]:
                V[AV_A_USER_RESPONSE] = "User not set."
                V[AV_A_RESULT] = AV_V_RESULT_ERROR
                result = MAVIS_FINAL
                output_av_pairs(V, result)
                buffer = ""
                continue

            tactype = V[AV_A_TACTYPE]
            if tactype == AV_V_TACTYPE_HOST:
                V[AV_A_TACPROFILE] = (
                    '{\n'
                    '    key = demo\n'
                    '    radius.key = demo\n'
                    '    tag = cust001,cust-ro\n'
                    '    welcome banner = "Hi! :-)"\n'
                    '    mavis backend = yes\n'
                    '}'
                )
                V[AV_A_RESULT] = AV_V_RESULT_OK
                result = MAVIS_FINAL
                output_av_pairs(V, result)
                buffer = ""
                continue

            if tactype == AV_V_TACTYPE_DACL:
                V[AV_A_TACPROFILE] = (
                    '{\n'
                    '    data = "\n'
                    '        permit ip any any\n'
                    '    "\n'
                    '}'
                )
                V[AV_A_RESULT] = AV_V_RESULT_OK
                result = MAVIS_FINAL
                output_av_pairs(V, result)
                buffer = ""
                continue

            # User profile
            V[AV_A_TACPROFILE] = (
                '{\n'
                '    tag = cust001,ro\n'
                '    profile {\n'
                '        script {\n'
                '            if (device.tag != user.tag)\n'
                '                deny\n'
                '            if (aaa.protocol == tacacs) {\n'
                '                if (service == shell) {\n'
                '                    if (cmd == "") {\n'
                '                        set priv-lvl = 15\n'
                '                        permit\n'
                '                    }\n'
                '                    if (user.tag == ro) {\n'
                '                        if (cmd =~ /^show /) permit\n'
                '                        if (cmd =~ /^ping /) permit\n'
                '                        if (cmd =~ /^traceroute /) permit\n'
                '                        deny\n'
                '                    }\n'
                '                    if (user.tag == rw)\n'
                '                        permit\n'
                '                }\n'
                '                deny\n'
                '            }\n'
                '            if (aaa.protocol == radius) {\n'
                '                set radius[Cisco:Cisco-AVPair] = "shell:priv-lvl=15"\n'
                '                set radius[Cisco:Cisco-AVPair] = "ACS:CiscoSecure-Defined-ACL=${dacl:demoacl}"\n'
                '                permit\n'
                '            }\n'
                '            deny\n'
                '        }\n'
                '    }\n'
                '}'
            )

            if tactype == AV_V_TACTYPE_INFO:
                V[AV_A_RESULT] = AV_V_RESULT_OK
                result = MAVIS_FINAL
                output_av_pairs(V, result)
                buffer = ""
                continue

            if tactype in (AV_V_TACTYPE_AUTH, AV_V_TACTYPE_CHPW):
                if not V[AV_A_PASSWORD]:
                    V[AV_A_USER_RESPONSE] = "Password not set."
                    V[AV_A_RESULT] = AV_V_RESULT_FAIL
                    result = MAVIS_FINAL
                    output_av_pairs(V, result)
                    buffer = ""
                    continue
                # Demo password check
                if V[AV_A_PASSWORD] != "demo":
                    V[AV_A_USER_RESPONSE] = "Permission denied."
                    V[AV_A_RESULT] = AV_V_RESULT_FAIL
                    result = MAVIS_FINAL
                    output_av_pairs(V, result)
                    buffer = ""
                    continue
                if tactype == AV_V_TACTYPE_AUTH:
                    V[AV_A_RESULT] = AV_V_RESULT_OK
                    result = MAVIS_FINAL
                    output_av_pairs(V, result)
                    buffer = ""
                    continue
                if tactype == AV_V_TACTYPE_CHPW:
                    if not V[AV_A_PASSWORD_NEW]:
                        V[AV_A_USER_RESPONSE] = "New password not set."
                        V[AV_A_RESULT] = AV_V_RESULT_FAIL
                        result = MAVIS_FINAL
                        output_av_pairs(V, result)
                        buffer = ""
                        continue
                    # Password change logic here
                    V[AV_A_RESULT] = AV_V_RESULT_OK
                    result = MAVIS_FINAL
                    output_av_pairs(V, result)
                    buffer = ""
                    continue

            # Default: output what we have
            output_av_pairs(V, result)
            buffer = ""
        else:
            buffer += line

if __name__ == "__main__":
    main()