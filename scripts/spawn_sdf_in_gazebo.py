#!/usr/bin/env python3

import argparse
import os
import sys

import rclpy
from rclpy.node import Node
from rclpy.utilities import remove_ros_args

from ed_object_models.sdf_tools import spawn_sdf_from_yaml

if __name__ == "__main__":
    rclpy.init(args=sys.argv)

    my_args = remove_ros_args(sys.argv)

    parser = argparse.ArgumentParser(description="Spawn a list of sdf models from a yaml file into Gazebo")
    parser.add_argument("yaml_path", type=str)
    parser.add_argument("--world", type=str, default="default", help="Name of the Gazebo world to spawn into")
    arguments = parser.parse_args(my_args[1:])

    yaml_path = arguments.yaml_path
    if not os.path.isabs(yaml_path):
        yaml_path = os.path.join(os.path.curdir, yaml_path)

    # Initialize ROS node
    node = Node("gazebo_object_spawner")

    spawn_sdf_from_yaml(yaml_path, node, arguments.world)

    rclpy.shutdown()
