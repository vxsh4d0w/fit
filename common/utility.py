#!/usr/bin/env python3
# -*- coding:utf-8 -*-
######
# -----
# MIT License
# 
# Copyright (c) 2022 FIT-Project and others
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----
###### 

from importlib import util
import os
import sys
import hashlib
import platform
import subprocess
import ntplib
import urllib.request
from   urllib.parse import urlparse
from datetime import datetime, timezone

from whois import NICClient, WhoisEntry, extract_domain, IPV4_OR_V6
import socket
import requests
requests.urllib3.disable_warnings()
import ssl
import scapy.all as scapy
from contextlib import redirect_stdout


from nslookup import Nslookup

def get_platform():

    platforms = {
        'linux1' : 'lin',
        'linux2' : 'lin',
        'darwin' : 'osx',
        'win32'  : 'win'
    }

    if sys.platform not in platforms:
        return 'other'

    return platforms[sys.platform]

if get_platform() == 'win':

    import winreg

    def get_list_of_programs_installed_on_windows(hive, flag):
        aReg = winreg.ConnectRegistry(None, hive)
        aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                            0, winreg.KEY_READ | flag)

        count_subkey = winreg.QueryInfoKey(aKey)[0]

        software_list = []

        for i in range(count_subkey):
            software = {}
            try:
                asubkey_name = winreg.EnumKey(aKey, i)
                asubkey = winreg.OpenKey(aKey, asubkey_name)
                software['name'] = winreg.QueryValueEx(asubkey, "DisplayName")[0]

                try:
                    software['version'] = winreg.QueryValueEx(asubkey, "DisplayVersion")[0]
                except EnvironmentError:
                    software['version'] = 'undefined'
                try:
                    software['publisher'] = winreg.QueryValueEx(asubkey, "Publisher")[0]
                except EnvironmentError:
                    software['publisher'] = 'undefined'
                software_list.append(software)
            except EnvironmentError:
                continue

        return software_list

    def program_is_installed(name):
        program = None
        is_istalled = False
        software_list = None
        if get_platform() == 'win':
            software_list = get_list_of_programs_installed_on_windows(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY) + \
                            get_list_of_programs_installed_on_windows(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY) + \
                            get_list_of_programs_installed_on_windows(winreg.HKEY_CURRENT_USER, 0)
        
        if software_list is not None:
            for software in software_list:
                if name in software['name']:
                    program = {'name':software['name'], 'version':software['version'], 'publisher':software['publisher']}
                    is_istalled = True
                    break

        return is_istalled

def calculate_hash(filename, algorithm):
    with open(filename, "rb") as f:
        file_hash = hashlib.new(algorithm)
        while chunk := f.read(8192):
            file_hash.update(chunk)

        return file_hash.hexdigest()

def get_ntp_date_and_time(server):
    try:
        ntpDate = None
        client = ntplib.NTPClient()
        response = client.request(server, version=3)
    except Exception as exception:
        return exception

    return datetime.fromtimestamp(response.tx_time, timezone.utc)


def whois(url, flags=0):

    ip_match = IPV4_OR_V6.match(url)
    if ip_match:
        domain = url
        try:
            result = socket.gethostbyaddr(url)
        except socket.herror as e:
            return e.strerror
        else:
            domain = extract_domain(result[0])
    else:
        domain = extract_domain(url)

    # try builtin client
    nic_client = NICClient()

    return nic_client.whois_lookup(None, domain.encode('idna'), flags)

def nslookup(url, dns_server, enable_verbose_mode, enable_tcp):
    url=urlparse(url)
    netloc = url.netloc

    if not netloc:
       return "Don't find Network location part in the URL"
    else: 
        dns_query = Nslookup(dns_servers=[dns_server], verbose=enable_verbose_mode, tcp=enable_tcp)
        ips_record = dns_query.dns_lookup(url.netloc)

        return '\n'.join(map(str, ips_record.response_full))

def traceroute(url, filename):
    url=urlparse(url)
    netloc = url.netloc

    if not netloc:
        print("Don't find Network location part in the URL")
    else: 
        with open(filename, 'w') as f:
            with redirect_stdout(f):
                ans, unans = scapy.sr(scapy.IP(dst=netloc, ttl=(1,22),id=scapy.RandShort())/scapy.TCP(flags=0x2), timeout=10)
                for snd,rcv in ans:
                    print(snd.ttl, rcv.src, isinstance(rcv.payload, scapy.TCP))

def get_headers_information(url):
    response = requests.get(url)
    
    return response.headers


def check_internet_connection(host='http://google.com'):
    try:
        urllib.request.urlopen(host)
        return True
    except:
        return False
        

def check_if_peer_certificate_exist(url):
    with requests.get(url, stream=True, timeout=10, verify=False) as response:
        try:
            response.raw.connection.sock.getpeercert()
            return True
        except Exception as e:
            return False

def get_peer_PEM_cert(url, port=443, timeout=10):
    url=urlparse(url)
    netloc = url.netloc
    
    if not netloc:
       return None
    else: 
        context = ssl.create_default_context()
        conn = socket.create_connection((netloc, port))
        sock = context.wrap_socket(conn, server_hostname=netloc)
        sock.settimeout(timeout)

        try:
            der_cert = sock.getpeercert(True)
        finally:
            sock.close()

        return ssl.DER_cert_to_PEM_cert(der_cert)

def save_PEM_cert_to_CER_cert(filename, certificate):
    try:
        with open(filename, 'w+') as cer_file:
            if(sys.version_info[0] >= 3):
                cer_file.write(certificate)
            else:
                cer_file.write(certificate)
    except IOError:
        print('Exception:  {0}'.format(IOError.strerror))



def import_modules(start_path, start_module_name = ""):
    
    py_files = []
    exclude = set(['test'])
    for root, dirs, files in os.walk(start_path):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                    if file.endswith(".py") and not file.endswith('__.py'): 
                            py_files.append(os.path.join(start_path, root, file))

    for py_file in py_files:
            module_name = start_module_name + "." + os.path.split(py_file)[-1].rsplit( ".", 1 )[ 0 ]
            spec = util.spec_from_file_location(module_name, py_file)
            module = util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)


