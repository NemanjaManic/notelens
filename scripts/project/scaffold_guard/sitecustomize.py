"""Review-only Python network guard; allow loopback and reject external sockets/DNS."""

import ipaddress
import json
import os
import socket

GUARD_ACTIVE = True


def allowed(host):
    if host is None or host in ('localhost', b'localhost'):
        return True
    try:
        if isinstance(host, bytes):
            host = host.decode('ascii')
        address = ipaddress.ip_address(host)
        return address.is_loopback or bool(getattr(address, 'ipv4_mapped', None) and address.ipv4_mapped.is_loopback)
    except (ValueError, TypeError, UnicodeError):
        return False


def reject(operation):
    log = os.environ.get('NOTELENS_REVIEW_NETWORK_LOG')
    if log:
        with open(log, 'a', encoding='utf-8') as output:
            output.write(json.dumps({'operation': operation, 'blocked': True}) + '\n')
    raise OSError('Review guard blocked non-loopback networking')


original_connect = socket.socket.connect
original_connect_ex = socket.socket.connect_ex
original_getaddrinfo = socket.getaddrinfo
original_gethostbyname = socket.gethostbyname
original_gethostbyname_ex = socket.gethostbyname_ex


def connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and not allowed(address[0]):
        reject('connect')
    return original_connect(self, address)


def connect_ex(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and not allowed(address[0]):
        reject('connect_ex')
    return original_connect_ex(self, address)


def getaddrinfo(host, *args, **kwargs):
    if not allowed(host):
        reject('getaddrinfo')
    return original_getaddrinfo(host, *args, **kwargs)


def gethostbyname(host):
    if not allowed(host):
        reject('gethostbyname')
    return original_gethostbyname(host)


def gethostbyname_ex(host):
    if not allowed(host):
        reject('gethostbyname_ex')
    return original_gethostbyname_ex(host)


socket.socket.connect = connect
socket.socket.connect_ex = connect_ex
socket.getaddrinfo = getaddrinfo
socket.gethostbyname = gethostbyname
socket.gethostbyname_ex = gethostbyname_ex
