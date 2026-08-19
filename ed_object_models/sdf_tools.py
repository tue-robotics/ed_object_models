import glob
import os
import yaml

import rclpy
from rclpy.node import Node

from ros_gz_interfaces.srv import SpawnEntity
from geometry_msgs.msg import Pose, Point, Quaternion
from tf_transformations import quaternion_from_euler


def get_sdf_string(model_type: str, node: Node) -> str:
    """
    Get sdf string of a specific model. Searching in GZ_SIM_RESOURCE_PATH

    :param model_type: name of the model
    :param node: node used for logging
    :return: xml string, empty in case of error
    """
    # Get paths in $GZ_SIM_RESOURCE_PATH
    model_paths = os.environ["GZ_SIM_RESOURCE_PATH"].split(os.pathsep)

    # Search for model folder in $GZ_SIM_RESOURCE_PATH
    model_dir = None
    for path in model_paths:
        test_model_dir = os.path.join(path, model_type)
        if os.path.isdir(test_model_dir):
            model_dir = test_model_dir
            break

    # Return error when folder could not be found
    if model_dir is None:
        node.get_logger().warn(f"Couldn't find model directory of model type: '{model_type}' in GZ_SIM_RESOURCE_PATH")
        return ""

    # Search for sdf file
    sdf_model_path = os.path.join(model_dir, "model.sdf")
    if not os.path.isfile(sdf_model_path):
        # If is no model.sdf exists and there are one or more sdf files, return
        # the last alphabetically which is assumed to be for the highest sdf version.
        sdf_list = glob.glob(os.path.join(model_dir, "*.sdf"))
        if sdf_list:
            sdf_model_path = max(sdf_list)
        else:
            # Return error when no sdf file could be found
            node.get_logger().warn(f"No sdf file was found for type: '{model_type}'")
            return ""

    with open(sdf_model_path, "r") as f:
        return f.read()


def spawn_sdf_from_yaml(yaml_path: str, node: Node, world: str = "default") -> None:
    """
    Spawns a list of sdf models from a yaml file into Gazebo.

    :param yaml_path: path to a yaml file.
    :param node: node used to call the spawn service and for logging
    :param world: name of the Gazebo world to spawn the models into

    The yaml file that yaml_path points to should be a dictonary or a list of dictionaries.
    Each dictionary should at least contain the keys id, type, x, y and z,
    additional optional keys are roll, pitch and yaw. The meaning of the keys are:
    - id: a string which defines the name given to the loaded model in gazebo.
    - type: a string which refers to a sdf model name contained within GZ_SIM_RESOURCE_PATH.
    - x, y, z: floats representing the coordinates at which the model is spawned.
    - roll, pitch, yaw: floats representing Euler angles, if not used they are set to zero.
    An example of such a dictionary list item is given below:
    - {id: "coke-1", type: "coke_can", x: 3.196, y: 4.652, z: 0.87, roll: 0.5, pitch: 1.57}

    Requires a ros_gz_bridge parameter_bridge exposing the world's create service, e.g.:
    ros2 run ros_gz_bridge parameter_bridge /world/<world>/create@ros_gz_interfaces/srv/SpawnEntity
    """

    # Wait until gazebo is ready to spawn entities
    service_name = f"/world/{world}/create"
    spawn_entity_client = node.create_client(SpawnEntity, service_name)
    if not spawn_entity_client.wait_for_service(timeout_sec=30):
        node.get_logger().error(f"Service '{service_name}' is not available")
        return

    if not os.path.isfile(yaml_path):  # Check if yaml_path is a path to a file.
        if os.path.isfile(yaml_path + ".yaml"):
            yaml_path = yaml_path + ".yaml"
        elif os.path.isfile(yaml_path + ".yml"):
            yaml_path = yaml_path + ".yml"
        else:
            node.get_logger().error("Could not find input file:" + yaml_path)
            return

    with open(yaml_path, "r") as f:
        items = yaml.safe_load(f)

    if not isinstance(items, list):
        if isinstance(items, dict):
            items = [items]
        else:
            node.get_logger().fatal(
                f"Loaded yaml file: {yaml_path}, but it didn't result in a 'list' or a 'dict' but in a: '{type(items)}'"
            )

    # Iterate over objects and spawn
    for item in items:
        # Define object pose
        object_pose = Pose()
        object_pose.position = Point(x=item["x"], y=item["y"], z=item["z"])
        q = quaternion_from_euler(item.get("roll", 0), item.get("pitch", 0), item.get("yaw", 0))
        object_pose.orientation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])

        sdf_string = get_sdf_string(item["type"], node)
        if not sdf_string:
            continue

        # Spawn object
        request = SpawnEntity.Request()
        request.entity_factory.name = item["id"]
        request.entity_factory.sdf = sdf_string
        request.entity_factory.pose = object_pose
        request.entity_factory.relative_to = "world"

        future = spawn_entity_client.call_async(request)
        rclpy.spin_until_future_complete(node, future)
        outcome = future.result()
        if outcome is None:
            node.get_logger().warn(f"Service call failed: {future.exception()}")
        elif not outcome.success:
            node.get_logger().warn(f"Failed to spawn '{item['id']}'")
