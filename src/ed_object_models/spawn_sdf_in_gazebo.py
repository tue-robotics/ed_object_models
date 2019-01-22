#! /usr/bin/python

import rospy
import yaml
import os
import glob

from rospkg import RosPack
from gazebo_msgs.srv import SpawnModel
from geometry_msgs.msg import Pose


def from_yaml(yaml_file):
    ''' Spawns a list of sdf files from a yaml file into Gazebo.
    :param yaml_file:
    :return:
    '''

    # Initialize ROS node
    rospy.init_node('gazebo_simulator_object_spawner')

    # Wait until gazebo is ready to spawn sdf models
    rospy.wait_for_service('gazebo/spawn_sdf_model')
    spawn_model_prox = rospy.ServiceProxy('gazebo/spawn_sdf_model', SpawnModel)

    # Load yaml with list of objects that need to be loaded
    yaml_file_path = None
    if os.path.isfile(yaml_file):   # Check if yaml_file is path to a file
        yaml_file_path = yaml_file
    else:   # Check if yaml_file is path to a file in fast_simulator_data
        package_path = RosPack().get_path('fast_simulator_data')
        if os.path.isfile(package_path + yaml_file):
            yaml_file_path = package_path + yaml_file

    if yaml_file_path is None:
        print('Warning: Could not find yaml file.')
        return

    with open(yaml_file_path, 'r') as f:
        data = yaml.safe_load(f)

    # Get paths in $GAZEBO_MODEL_PATH
    model_paths = os.environ['GAZEBO_MODEL_PATH'].split(os.pathsep)

    # Iterate over objects and spawn
    for sod in data:
        # Define object pose
        object_pose = Pose()
        object_pose.position.x = sod['x']
        object_pose.position.y = sod['y']
        object_pose.position.z = sod['z']

        # Search for model folder in $GAZEBO_MODEL_PATH
        model_path = None
        for path in model_paths:
            if os.path.isdir(path + '/' + sod['type']):
                model_path = path + '/' + sod['type']

        # Return error when folder could not be found
        if model_path is None:
            print('Warning: Could not find model with the specified name in GAZEBO_MODEL_PATH.')
            continue

        # Search for sdf file
        sdf_model_path = None
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
        spawn_model_prox(sod['id'], sdf_file, 'spawned_objects', object_pose, 'world')
