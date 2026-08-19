#!/usr/bin/env python3

import sys

from ed_interfaces.srv import SimpleQuery
import PyKDL as kdl
import rclpy
from rclpy.node import Node

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Please provide robot name")
        sys.exit(1)

    robot_name = sys.argv[1]

    rclpy.init(args=sys.argv)
    node = Node("dump_ed")

    client = node.create_client(SimpleQuery, f"/{robot_name}/ed/simple_query")
    if not client.wait_for_service(timeout_sec=30):
        print(f"Service call failed: /{robot_name}/ed/simple_query not available")
        rclpy.shutdown()
        sys.exit(1)

    future = client.call_async(SimpleQuery.Request())
    rclpy.spin_until_future_complete(node, future)
    res = future.result()
    if res is None:
        print(f"Service call failed: {future.exception()}")
        rclpy.shutdown()
        sys.exit(1)

    for e in res.entities:
        if not e.has_shape:
            continue

        if e.id.startswith(robot_name):
            continue

        q_msg = e.pose.orientation
        q = kdl.Rotation.Quaternion(q_msg.x, q_msg.y, q_msg.z, q_msg.w)

        yaw = q.GetRPY()[2]  # 0:.2f

        print(f"- id: {e.id}")
        print(f"  type: {e.type}")

        pose = e.pose.position
        if abs(yaw) > 0.001:
            print(f"  pose: {{ x: {pose.x}, y: {pose.y}, z: {pose.z}, Z: {yaw:.3f} }}")
        else:
            print(f"  pose: {{ x: {pose.x}, y: {pose.y}, z: {pose.z} }}")

    rclpy.shutdown()
