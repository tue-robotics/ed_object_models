import glob
import os
import yaml

import rospy

from gazebo_msgs.srv import SpawnModel
from geometry_msgs.msg import Pose, Point, Quaternion
from tf_conversions.transformations import quaternion_from_euler


def get_sdf_string(model_type):
    """
    Get sdf string of a specific model. Searching in GAZEBO_MODEL_PATH

    :param model_type: name of the model
    :type model_type: str
    :return: xml string, empty in case of error
    :rtype: str
    """
    # Get paths in $GAZEBO_MODEL_PATH
    model_paths = os.environ["GAZEBO_MODEL_PATH"].split(os.pathsep)

    # Search for model folder in $GAZEBO_MODEL_PATH
    model_dir = None
    for path in model_paths:
        test_model_dir = os.path.join(path, model_type)
        if os.path.isdir(test_model_dir):
            model_dir = test_model_dir
            break

    # Return error when folder could not be found
    if model_dir is None:
        rospy.logwarn("Couldn't find model directory of model type: '{}' in GAZEBO_MODEL_PATH".format(model_type))
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
            rospy.logwarn("No sdf file was found for type: '{}'".format(model_type))
            return ""

    with open(sdf_model_path, "r") as f:
        return f.read()


def spawn_sdf_from_yaml(yaml_path):
    """
    Spawns a list of sdf models from a yaml file into Gazebo.

    :param yaml_path: path to a yaml file.
    :type yaml_path: str

    The yaml file that yaml_path points to should be a dictonary or a list of dictionaries.
    Each dictionary should at least contain the keys id, type, x, y and z,
    additional optional keys are roll, pitch and yaw. The meaning of the keys are:
    - id: a string which defines the name given to the loaded model in gazebo.
    - type: a string which refers to a sdf model name contained within GAZEBO_MODEL_PATH.
    - x, y, z: floats representing the coordinates at which the model is spawned.
    - roll, pitch, yaw: floats representing Euler angles, if not used they are set to zero.
    An example of such a dictionary list item is given below:
    - {id: "coke-1", type: "coke_can", x: 3.196, y: 4.652, z: 0.87, roll: 0.5, pitch: 1.57}
    """

    # Wait until gazebo is ready to spawn sdf models
    rospy.wait_for_service("gazebo/spawn_sdf_model", 30)
    spawn_model_srv = rospy.ServiceProxy("gazebo/spawn_sdf_model", SpawnModel)

    if not os.path.isfile(yaml_path):   # Check if yaml_path is a path to a file.
        if os.path.isfile(yaml_path + ".yaml"):
            yaml_path = yaml_path + ".yaml"
        elif os.path.isfile(yaml_path + ".yml"):
            yaml_path = yaml_path + ".yml"
        else:
            rospy.logerr("Could not find input file:" + yaml_path)
            return

    with open(yaml_path, "r") as f:
        items = yaml.safe_load(f)

    if not isinstance(items, list):
        if isinstance(items, dict):
            items = [items]
        else:
            rospy.logfatal("Loaded yaml file: {}, but it didn't result in a 'list' or a 'dict' but in a: '{}'").format(
                yaml_path, type(items))

    # Iterate over objects and spawn
    for item in items:
        # Define object pose
        object_pose = Pose()
        object_pose.position = Point(item["x"], item["y"], item["z"])
        object_pose.orientation = Quaternion(*quaternion_from_euler(item.get("roll", 0),
                                                                    item.get("pitch", 0),
                                                                    item.get("yaw", 0)))

        sdf_string = get_sdf_string(item["type"])
        if not sdf_string:
            continue

        # Spawn object
        outcome = spawn_model_srv.call(item["id"], sdf_string, "spawned_objects", object_pose, "world")
        if not outcome.success:
            rospy.logwarn(outcome.status_message)
