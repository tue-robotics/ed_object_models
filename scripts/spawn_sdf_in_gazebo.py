#!/usr/bin/env python3

import os
import sys

import rclpy
from rclpy.node import Node
from rclpy.utilities import remove_ros_args

from ed_object_models.sdf_tools import spawn_sdf_from_yaml

if __name__ == "__main__":
    rclpy.init(args=sys.argv)

    my_args = remove_ros_args(sys.argv)
    # Initialize ROS node
    node = Node("gazebo_object_spawner")

    yaml_path = my_args[1]
    if not os.path.isabs(yaml_path):
        yaml_path = os.path.join(os.path.curdir, yaml_path)

    spawn_sdf_from_yaml(yaml_path, node)

    rclpy.shutdown()
