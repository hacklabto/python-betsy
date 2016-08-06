#
# Protocol handling for Betsy tiles
#
# Copyright (c) 2016 Peter McCormick.
#

import socket
from time import time

def chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]

class CommandSocket(object):
    UDP_PORT                    = 48757         # 0xBE75
    IPV6_ALL_NODES_MULTICAST    = 'ff02::1'
    DPC_DATA_CHUNK_SIZE         = 1024

    def __init__(self, ifdev):
        self._ifdev = ifdev
        self._all_nodes = self.get_ipv6_addr_info(self.IPV6_ALL_NODES_MULTICAST)
        self._sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    def get_ipv6_addr_info(self, addr):
        addrinfo = socket.getaddrinfo(addr + '%' + self._ifdev, self.UDP_PORT, socket.AF_INET6, socket.SOCK_DGRAM)
        assert len(addrinfo) == 1
        return addrinfo[0][4]

    def send_commands(self, commands, addr):
        if isinstance(commands, str):
            pkt = commands.encode('utf-8')
        else:
            pkt = b';'.join([ cmd.encode('utf-8') for cmd in commands ])

        return self._sock.sendto(pkt, addr)

    def pack_one_payload_command(self, command, payload, addr):
        pkt = command.encode('utf-8') + b';' + payload
        return self._sock.sendto(pkt, addr)

    def recvfrom(self, timeout=None):
        if timeout is not None:
            self._sock.settimeout(timeout)

        (data, addr) = self._sock.recvfrom(1500)
        return (data, addr)

    def recv_for_period(self, period):
        now = start = time()
        stop = start + period
        remaining = stop - now

        recvs = []

        while now < stop:
            try:
                data_addr = self.recvfrom(timeout=remaining)
            except socket.timeout:
                break

            recvs.append(data_addr)
            now = time()
            remaining = stop - now

        return recvs

    def dpc_data(self, addr, buf_i, data):
        offs = 0
        for sub_data in chunk(data, self.DPC_DATA_CHUNK_SIZE):
            self.pack_one_payload_command("dpc data %d %d" % (buf_i, offs), sub_data, addr)
            offs += len(sub_data)

    def dpc_upload(self, addr, buf_i):
        self.send_commands("dpc upload %d" % buf_i, addr)
