#! /usr/bin/python

import rospy
import yaml
import os
import glob

from gazebo_msgs.srv import SpawnModel
from geometry_msgs.msg import Pose, Point, Quaternion
from tf.transformations import quaternion_from_euler

def from_yaml(yaml_path):
    '''
    Spawns a list of sdf files from a yaml file into Gazebo.
    :param yaml_path: path to a yaml file.
    :type yaml_path: str
    :return: Spawns the sdf models.

    The yaml file that yaml_path points to should be a list of dictionaries.
    Each dictionary should at least contain the keys id, type, x, y and z,
    additional optional keys are roll, pitch and yaw. The meaning of the keys are:
    - id: a string which defines the name given to the loaded model in gazebo.
    - type: a string which refers to a sdf model name contained within GAZEBO_MODEL_PATH.
    - x, y, z: floats representing the coordinates at which the model is spawned.
    - roll, pitch, yaw: floats representing Euler angles, if not used they are set to zero.
    An example of such a dictionary list item is given below:
    - {id: "coke-1", type: "coke_can", x: 3.196, y: 4.652, z: 0.87, roll: 0.5, pitch: 1.57}
    '''

    # Initialize ROS node
    rospy.init_node('gazebo_simulator_object_spawner')

    # Wait until gazebo is ready to spawn sdf models
    rospy.wait_for_service('gazebo/spawn_sdf_model')
    spawn_model_prox = rospy.ServiceProxy('gazebo/spawn_sdf_model', SpawnModel)

    # Load yaml with list of objects that need to be loaded
    if not os.path.isfile(yaml_path):   # Check if yaml_path is a path to a file.
        print('Warning: Could not find ' + yaml_path)
        return

    with open(yaml_path, 'r') as f:
        items = yaml.safe_load(f)

    # Get paths in $GAZEBO_MODEL_PATH
    model_paths = os.environ['GAZEBO_MODEL_PATH'].split(os.pathsep)

    # Iterate over objects and spawn
    for item in items:
        # Define object pose
        object_pose = Pose()
        object_pose.position = Point(item['x'], item['y'], item['z'])
        object_pose.orientation = Quaternion(*quaternion_from_euler(item.get('roll', 0),
                                                                    item.get('pitch', 0),
                                                                    item.get('yaw', 0)))

        # Search for model folder in $GAZEBO_MODEL_PATH
        model_path = None
        for path in model_paths:
            if os.path.isdir(os.path.join(path, item['type'])):
                model_path = os.path.join(path, item['type'])

        # Return error when folder could not be found
        if not model_path:
            print('Warning: Could not find model with the name' + item['type'] + 'in GAZEBO_MODEL_PATH.')
            continue

        # Search for sdf file
        if os.path.isfile(os.path.join(model_path, 'model.sdf')):
            sdf_model_path = os.path.join(model_path, 'model.sdf')
        else:
            # If is no model.sdf exists and there are one or more sdf files, return
            # the last alphabetically which is assumed to be for the highest sdf version.
            sdf_list = glob.glob(os.path.join(model_path, '*.sdf'))
            if sdf_list:
                sdf_model_path = max(sdf_list)
            else:
                # Return error when no sdf file could be found
                print('Warning: No sdf file was found.')
                continue

        with open(sdf_model_path, 'r') as f:
            sdf_file = f.read()

        # Spawn object
        outcome = spawn_model_prox(item['id'], sdf_file, 'spawned_objects', object_pose, 'world')
        if not outcome.success:
            print(outcome.status_message)
