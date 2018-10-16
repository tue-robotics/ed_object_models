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
sdf_dict[sdf_dict.keys()[0]] = {model_name: {'link name="link"': {},
                                             'pose': [0, 0, 0, 0, 0, 0],
                                             'static': 'true'}}
print sdf_dict
# print sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]['link name="link"']

with open("model.yaml", 'r') as stream:
    try:
        x = yaml.load(stream)
        # print(x)
    except yaml.YAMLError as exc:
        print(exc)
print(x)
# test = {'sdf version="1.6"': {'model name = "couch"': {'pose': [0, 0, 0.5, 0, 0, 0], 'static': 'false'}}}
#
# xml = dicttoxml.dicttoxml(test)
# myfile = open("xmltest.xml", "w")
# myfile.write(xml)

# Filling the empty dictionary
if file_type == "object":
    if isinstance(x, dict):
        counter = 0
        for shape_items in x['shape']['compound']:
            if shape_items.keys()[0] == "cylinder":
                print "Feature not yet implemented in this script"
            elif shape_items.keys()[0] == "box":
                sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]['link name="link"']\
                    .update({'collision name="{}"'.format(shape_items['box']['#']):
                                                 {'pose': [shape_items['box']['pose']['x'],
                                                           shape_items['box']['pose']['y'],
                                                           shape_items['box']['pose']['z'],
                                                           0,
                                                           0,
                                                           0],
                                                  'geometry': {'box': {'size': [shape_items['box']['size']['x'],
                                                                                shape_items['box']['size']['y'],
                                                                                shape_items['box']['size']['z']]}}}})
                sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]['link name="link"'] \
                    .update({'visual name="{} visual"'.format(shape_items['box']['#']):
                                 {'pose': [shape_items['box']['pose']['x'],
                                           shape_items['box']['pose']['y'],
                                           shape_items['box']['pose']['z'],
                                           0,
                                           0,
                                           0],
                                  'geometry': {'box': {'size': [shape_items['box']['size']['x'],
                                                                shape_items['box']['size']['y'],
                                                                shape_items['box']['size']['z']]}}}})
            counter = counter + 1
            print shape_items

        # sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]
        for key in x:
            print "Dictionary item:", key

    elif isinstance(x, list):
        for item in x:
            print 'List item:', item
elif file_type == "room":
    print "Dictionary item:", key

print sdf_dict
