#! /usr/bin/python

import rospy
import yaml
import os
import glob

from rospkg import RosPack
from gazebo_msgs.srv import SpawnModel
from geometry_msgs.msg import Pose


def from_yaml(yaml_file, package_name='fast_simulator_data'):
    '''
    Spawns a list of sdf files from a yaml file into Gazebo.
    :param yaml_file: path to a yaml file.
    :type yaml_file: str
    :param package_name: name of a package from which the yaml file should be loaded.
    :type package_name: str
    :return: Spawns the sdf models.
    '''

    # Initialize ROS node
    rospy.init_node('gazebo_simulator_object_spawner')

    # Wait until gazebo is ready to spawn sdf models
    rospy.wait_for_service('gazebo/spawn_sdf_model')
    spawn_model_prox = rospy.ServiceProxy('gazebo/spawn_sdf_model', SpawnModel)

    # Load yaml with list of objects that need to be loaded
    package_path = RosPack().get_path(package_name)
    if os.path.isfile(package_path + yaml_file):   # Check if package_path + yaml_file is a path to a file.
        yaml_file_path = package_path + yaml_file
    else:
        print('Warning: Could not find yaml file.')
        return

    with open(yaml_file_path, 'r') as f:
        items = yaml.safe_load(f)

    # Get paths in $GAZEBO_MODEL_PATH
    model_paths = os.environ['GAZEBO_MODEL_PATH'].split(os.pathsep)

    # Iterate over objects and spawn
    for item in items:
        # Define object pose
        object_pose = Pose()
        object_pose.position.x = item['x']
        object_pose.position.y = item['y']
        object_pose.position.z = item['z']

        # Search for model folder in $GAZEBO_MODEL_PATH
        model_path = None
        for path in model_paths:
            if os.path.isdir(path + '/' + item['type']):
                model_path = path + '/' + item['type']

        # Return error when folder could not be found
        if not model_path:
            print('Warning: Could not find model with the specified name in GAZEBO_MODEL_PATH.')
            continue

        # Search for sdf file
        if os.path.isfile(model_path + '/model.sdf'):
            sdf_model_path = model_path + '/model.sdf'
        else:
            # If is no model.sdf exists and there are one or more sdf files, return
            # the last alphabetically which is assumed to be for the highest sdf version.
            sdf_list = sorted(glob.glob(model_path + '/*.sdf'))
            if sdf_list:
                sdf_model_path = sdf_list[-1]
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
