#!/usr/bin/env python3

import sys
import socket
import numpy as np
import time
import xml.etree.ElementTree as ET

import errno
# import rospy
# from std_msgs.msg import String

def create_rsi_xml_rob(act_joint_pos, setpoint_joint_pos, timeout_count, ipoc):
    q = act_joint_pos
    qd = setpoint_joint_pos
    root = ET.Element('Rob', {'TYPE':'KUKA'})
    ET.SubElement(root, 'RIst', {'X':'0.0', 'Y':'0.0', 'Z':'0.0',
                                 'A':'0.0', 'B':'0.0', 'C':'0.0'})
    ET.SubElement(root, 'RSol', {'X':'0.0', 'Y':'0.0', 'Z':'0.0',
                                 'A':'0.0', 'B':'0.0', 'C':'0.0'})
    ET.SubElement(root, 'AIPos', {'A1':str(q[0]), 'A2':str(q[1]), 'A3':str(q[2]),
                                  'A4':str(q[3]), 'A5':str(q[4]), 'A6':str(q[5])})
    ET.SubElement(root, 'ASPos', {'A1':str(qd[0]), 'A2':str(qd[1]), 'A3':str(qd[2]),
                                  'A4':str(qd[3]), 'A5':str(qd[4]), 'A6':str(qd[5])})
    ET.SubElement(root, 'Delay', {'D':str(timeout_count)})
    ET.SubElement(root, 'IPOC').text=str(ipoc)
    return ET.tostring(root)

def parse_rsi_xml_sen(data):
    root = ET.fromstring(data)
    AK = root.find('AK').attrib
    desired_joint_correction = np.array([AK['A1'], AK['A2'], AK['A3'],
                                         AK['A4'], AK['A5'], AK['A6']]).astype(np.float64)
    IPOC = root.find('IPOC').text
    return desired_joint_correction, int(IPOC)


# if __name__ == '__main__':
def main():
    node_name = 'kuka_rsi_simulation'
# rsi_act_pub = rospy.Publisher(node_name + '/rsi/state', String, queue_size=1)
# rsi_cmd_pub = rospy.Publisher(node_name + '/rsi/command', String, queue_size=1)

    cycle_time = 0.004
    act_joint_pos = np.array([0, -90, 90, 0, 90, 0]).astype(np.float64)
    cmd_joint_pos = act_joint_pos.copy()
    des_joint_correction_absolute = np.zeros(6)
    timeout_count = 0
    ipoc = 0

    # import argparse
    # parser = argparse.ArgumentParser(description='KUKA RSI Simulation')
    # parser.add_argument('--rsi_hw_iface_ip', default="127.0.0.1", help='The ip address of the RSI control interface (default=127.0.0.1)')
    # parser.add_argument('--rsi_hw_iface_port', default=49152, help='The port of the RSI control interface (default=49152)')
    # parser.add_argument('--sen', default='ImFree', help='Type attribute in RSI XML doc. E.g. <Sen Type:"ImFree">')
    # # Only parse known arguments
    # args, _ = parser.parse_known_args()
    # host = args.rsi_hw_iface_ip
    # port = int(args.rsi_hw_iface_port)
    # sen_type = args.sen

    host = "127.0.0.1"
    port = 49152
    sen_type = 'ImFree'


    # rospy.init_node(node_name)
    # rospy.loginfo('{}: Started'.format(node_name))

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # rospy.loginfo('{}, Successfully created socket'.format(node_name))
        print('{}, Successfully created socket'.format(node_name))
        s.settimeout(1)
    except socket.error as e:
        # rospy.logfatal('{}Could not create socket'.format(node_name))
        print('{}Could not create socket'.format(node_name))
        sys.exit()

    def shutdown_hook():
        # rospy.loginfo('{}: Shutting down'.format(node_name))
        print('{}: Shutting down'.format(node_name))
        s.close()

    # rospy.on_shutdown(shutdown_hook)

    # while not rospy.is_shutdown():
    while True:
        time.sleep(0.001)  # this is a hack, make this a ros2 node
        try:
            msg = create_rsi_xml_rob(act_joint_pos, cmd_joint_pos, timeout_count, ipoc)
            # rsi_act_pub.publish(str(msg))
            s.sendto(msg, (host, port))
            recv_msg, addr = s.recvfrom(1024)
            # rsi_cmd_pub.publish(str(recv_msg))
            des_joint_correction_absolute, ipoc_recv = parse_rsi_xml_sen(recv_msg)
            act_joint_pos = cmd_joint_pos + des_joint_correction_absolute
            ipoc += 1
            time.sleep(cycle_time / 2)
        except socket.timeout:
            # rospy.logwarn('{}: Socket timed out'.format(node_name))
            print('{}: Socket timed out'.format(node_name))
            timeout_count += 1
        except socket.error as e:
            if e.errno != errno.EINTR:
                raise


if __name__ == '__main__':
    main()
