#! /usr/bin/env python

from ed_msgs.srv import SimpleQuery
import rospy
import PyKDL as kdl
import sys


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Please provide robot name")
        sys.exit(1)

    robot_name = sys.argv[1]

    rospy.init_node("dump_ed")

    rospy.wait_for_service(f"/{robot_name}/ed/simple_query")
    try:
        ed_query = rospy.ServiceProxy(f"/{robot_name}/ed/simple_query", SimpleQuery)
        res = ed_query()

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

    except rospy.ServiceException as e:
        print(f"Service call failed: e")
