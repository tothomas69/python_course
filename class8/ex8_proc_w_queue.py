#!/usr/bin/env python
'''
Use processes and Netmiko to connect to each of the devices in the database. Execute
'show version' on each device. Use a queue to pass the output back to the parent process.
Record the amount of time required to do this.
'''
from __future__ import print_function, unicode_literals
from netmiko import ConnectHandler
from datetime import datetime
from multiprocessing import Process, Queue

import django
django.setup()

from net_system.models import NetworkDevice     # noqa


def show_version_queue(a_device, output_q):
    '''
    Use Netmiko to execute show version. Use a queue to pass the data back to
    the main process.
    '''
    output_dict = {}
    creds = a_device.credentials
    remote_conn = ConnectHandler(device_type=a_device.device_type,
                                 ip=a_device.ip_address,
                                 username=creds.username, password=creds.password,
                                 port=a_device.port, secret='', verbose=False)

    output = ('#' * 80) + "\n"
    output += remote_conn.send_command_expect("show version") + "\n"
    output += ('#' * 80) + "\n"
    output_dict[a_device.device_name] = output
    output_q.put(output_dict)


def main():
    '''
    Use processes and Netmiko to connect to each of the devices in the database. Execute
    'show version' on each device. Use a queue to pass the output back to the parent process.
    Record the amount of time required to do this.
    '''
    start_time = datetime.now()
    output_q = Queue(maxsize=20)
    devices = NetworkDevice.objects.all()

    procs = []
    for a_device in devices:
        my_proc = Process(target=show_version_queue, args=(a_device, output_q))
        my_proc.start()
        procs.append(my_proc)

    # Make sure all processes have finished
    for a_proc in procs:
        a_proc.join()

    while not output_q.empty():
        my_dict = output_q.get()
        for k, val in my_dict.items():
            print(k)
            print(val)

    print("\nElapsed time: " + str(datetime.now() - start_time))


if __name__ == "__main__":
    main()
