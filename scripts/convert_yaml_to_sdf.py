#!/usr/bin/env python

import sys
import yaml
import dicttoxml


# if len(sys.argv) <= 1:
#     print "Please provide a file as input"
#     sys.exit(1)

# Create an empty dictionary in SDF format, which can later on be exported to XML after filling below.
sdf_dict = {'sdf version="1.6"': {}}

# First determine type of model.yaml
# Raw input can be replaced by fancier read_option in create-model.py
# file_type = raw_input("File type ('room' or 'object'): ")
# model_name = raw_input("Model name: ")

# Temporary replacements of user input
file_type = "object"
name = "couch"

model_name = 'model name="{}"'.format(name)
# print sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]['link name="link"']

with open("model.yaml", 'r') as stream:
    try:
        x = yaml.load(stream)
        # print(x)
    except yaml.YAMLError as exc:
        print(exc)
print(x)

# TEST CODE FOR EXPORTING TO XML, NOT WORKING CORRECTLY
# test = {'sdf version="1.6"': {'model name = "couch"': {'pose': [0, 0, 0.5, 0, 0, 0], 'static': 'false'}}}
#
# xml = dicttoxml.dicttoxml(test)
# myfile = open("xmltest.xml", "w")
# myfile.write(xml)

# Filling the empty dictionary
if file_type == "object":
    # Is object, so create a (static) model type SDF dictionary (as opposed to world), with a default pose
    sdf_dict[sdf_dict.keys()[0]] = {model_name: {'link name="link"': {},
                                                 'pose': [0, 0, 0, 0, 0, 0],
                                                 'static': 'true'}}
    sdf_dict_link_level = sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]['link name="link"']
    if isinstance(x, dict):
        shape_items_names = dict()
        for shape_items in x['shape']['compound']:
            compound_type = shape_items.keys()[0]

            # Check if compound type has name ('#' in yaml)
            if '#' not in shape_items[compound_type]:
                shape_items[compound_type]['#'] = compound_type

            # Create names for different elements in the compound, making sure to avoid overwriting duplicate names
            # by adding a counter for duplicate names. I.e. a name list of 'Leg', 'Leg' would become 'Leg', 'Leg02'
            if 'collision name="{}"'.format(shape_items[compound_type]['#']) in sdf_dict_link_level:
                shape_items_names[shape_items[compound_type]['#']] += 1
                box_name = shape_items[compound_type]['#'] + "{:02d}".format(shape_items_names[shape_items\
                    [compound_type]['#']])
            else:
                box_name = shape_items[compound_type]['#']
                shape_items_names[shape_items[compound_type]['#']] = 1

            shape_items_pose = [0, 0, 0, 0, 0, 0]
            # Check if pose is in same dictionary level as compound type or not
            if 'pose' in shape_items:
                # Check if coordinates are in pose, if so overwrite default 0
                if 'x' in shape_items['pose']:
                    shape_items_pose[0] = shape_items['pose']['x']
                elif 'y' in shape_items['pose']:
                    shape_items_pose[1] = shape_items['pose']['y']
                elif 'z' in shape_items['pose']:
                    shape_items_pose[2] = shape_items['pose']['z']
            elif 'pose' in shape_items[compound_type]:
                # If 'pose' is in compound_type then check if coordinates are in that level and overwrite default 0
                if 'x' in shape_items[compound_type]['pose']:
                    shape_items_pose[0] = shape_items[compound_type]['pose']['x']
                elif 'y' in shape_items[compound_type]['pose']:
                    shape_items_pose[1] = shape_items[compound_type]['pose']['y']
                elif 'z' in shape_items[compound_type]['pose']:
                    shape_items_pose[2] = shape_items[compound_type]['pose']['z']

            if compound_type == "cylinder":


                # sdf_dict_link_level.update({'collision name="{}"'.format(box_name):
                #                                 {'pose': shape_items_pose,
                #                                  'geometry': {'cylinder': {'radius': ,
                #                                                            'length': }}}})
                # sdf_dict_link_level.update({'visual name="{} visual"'.format(box_name):
                #                                 {'pose': shape_items_pose,
                #                                  'geometry': {'cylinder': {'size': shape_items_size}}}})

                print "Feature not yet implemented in this script"
            elif compound_type == "box":

                shape_items_size = [shape_items['box']['size']['x'],
                                    shape_items['box']['size']['y'],
                                    shape_items['box']['size']['z']]

                sdf_dict_link_level.update({'collision name="{}"'.format(box_name):
                                                {'pose': shape_items_pose,
                                                 'geometry': {'box': {'size': shape_items_size}}}})
                sdf_dict_link_level.update({'visual name="{} visual"'.format(box_name):
                                                {'pose': shape_items_pose,
                                                 'geometry': {'box': {'size': shape_items_size}}}})

        # sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]
        for key in x:
            print "Dictionary item:", key

    elif isinstance(x, list):
        for item in x:
            print 'List item:', item
elif file_type == "room":
    print "Dictionary item:", key

print "==============\nSDF Dictionary = " + str(sdf_dict)
