#!/usr/bin/env python

import sys
import yaml
import dicttoxml
from xml.dom.minidom import parseString


def fill_pose(yaml_dict):
    pose = [0, 0, 0, 0, 0, 0]
    # Check if coordinates are in pose, if so overwrite default 0
    if 'x' in yaml_dict['pose']:
        pose[0] = yaml_dict['pose']['x']
    if 'y' in yaml_dict['pose']:
        pose[1] = yaml_dict['pose']['y']
    if 'z' in yaml_dict['pose']:
        pose[2] = yaml_dict['pose']['z']
    if 'X' in yaml_dict['pose']:
        pose[3] = yaml_dict['pose']['X']
    if 'Y' in yaml_dict['pose']:
        pose[4] = yaml_dict['pose']['Y']
    if 'Z' in yaml_dict['pose']:
        pose[5] = yaml_dict['pose']['Z']

    pose = str(pose).replace("[", "").replace("]", "").replace(",", "")
    return pose


def fill_shapes(yaml_dict, red=0, green=0, blue=0):
    object_color = [red, green, blue, 1]
    shape_items_names = dict()
    sdf_dict = {}

    if 'compound' in yaml_dict:
        geometries = yaml_dict['compound']
    else:
        geometries = yaml_dict

    for shape_items in geometries:
        compound_type = shape_items.keys()[0]

        # Check if compound type has name ('#' in yaml)
        if '#' not in shape_items[compound_type]:
            shape_items[compound_type]['#'] = compound_type

        # Create names for different elements in the compound, making sure to avoid overwriting duplicate names
        # by adding a counter for duplicate names. I.e. a name list of 'Leg', 'Leg' would become 'Leg', 'Leg02'
        if 'collision name="{}"'.format(shape_items[compound_type]['#']) in sdf_dict:
            shape_items_names[shape_items[compound_type]['#']] += 1
            shape_name = shape_items[compound_type]['#'] + "{:02d}".format(shape_items_names[shape_items \
                [compound_type]['#']])
        else:
            shape_name = shape_items[compound_type]['#']
            shape_items_names[shape_items[compound_type]['#']] = 1

        # Check if pose is in same dictionary level as compound type or not
        if 'pose' in shape_items:
            # Check if coordinates are in pose, if so overwrite default 0
            shape_items_pose = fill_pose(shape_items)
        elif 'pose' in shape_items[compound_type]:
            # If 'pose' is in compound_type then check if coordinates are in that level and overwrite default 0
            shape_items_pose = fill_pose(shape_items[compound_type])

        if compound_type == "cylinder":

            sdf_dict.update({'collision name="{}"'.format(shape_name):
                                 {'pose': shape_items_pose,
                                  'geometry': {'cylinder': {'radius': shape_items['cylinder']['radius'],
                                                            'length': shape_items['cylinder']['height']}}},
                             'visual name="{} visual"'.format(shape_name):
                                 {'pose': shape_items_pose,
                                  'geometry': {'cylinder': {'radius': shape_items['cylinder']['radius'],
                                                            'length': shape_items['cylinder']['height']}}}
                             })
            if object_color != [0, 0, 0, 1]:
                sdf_dict['visual name="{} visual"'.format(shape_name)] = \
                    {'material': {'ambient': str(object_color).replace("[", "").replace("]", "").replace(",", "")}}

        elif compound_type == "box":

            shape_items_size = [shape_items['box']['size']['x'],
                                shape_items['box']['size']['y'],
                                shape_items['box']['size']['z']]
            shape_items_size = str(shape_items_size).replace("[", "").replace("]", "").replace(",", "")

            sdf_dict.update({'collision name="{}"'.format(shape_name):
                                 {'pose': shape_items_pose,
                                  'geometry': {'box': {'size': shape_items_size}}},
                             'visual name="{} visual"'.format(shape_name):
                                 {'pose': shape_items_pose,
                                  'geometry': {'box': {'size': shape_items_size}}}
                             })
            if object_color != [0, 0, 0, 1]:
                sdf_dict['visual name="{} visual"'.format(shape_name)] = \
                    {'material': {'ambient': str(object_color).replace("[", "").replace("]", "").replace(",", "")}}

    return sdf_dict


def main():
    # if len(sys.argv) <= 1:
    #     print "Please provide a file as input"
    #     sys.exit(1)

    # Create an empty dictionary in SDF format, which can later on be exported to XML after filling below.
    sdf_dict = {'sdf version="1.6"': {}}

    # First determine type of model.yaml
    # Raw input can be replaced by fancier read_option in create-model.py
    # file_type = raw_input("File type ('world' or 'object'): ")
    # model_name = raw_input("Model name: ")

    # Temporary replacements of user input
    file_type = "object"

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
        model_name = 'model name="{}"'.format("couch")
        # Is object, so create a (static) model type SDF dictionary (as opposed to world), with a default pose
        sdf_dict[sdf_dict.keys()[0]] = {model_name: {'link name="link"': {},
                                                     'pose': "0 0 0 0 0 0",
                                                     'static': 'true'}}
        sdf_dict_model_level = sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]
        sdf_dict_link_level = sdf_dict_model_level['link name="link"']

        if isinstance(x, dict):
            if 'color' in x:
                red = x['color']['red']
                green = x['color']['red']
                blue = x['color']['blue']
                sdf_dict_link_level.update(fill_shapes(x['shape'], red, green, blue))
            else:
                sdf_dict_link_level.update(fill_shapes(x['shape']))

            for area_items in x['areas']:
                # sdf_dict_custom_level[area_items['name']] = {}
                # if 'offset' in area_items:
                #     sdf_dict_custom_level[area_items['name']].update({'offset': area_items['offset']})
                #
                # if 'shape' in area_items:
                #     sdf_dict_custom_level[area_items['name']].update(fill_shapes(area_items['shape']))

                print area_items

            # sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]
            for key in x:
                print "Dictionary item:", key

        elif isinstance(x, list):
            for item in x:
                print 'List item:', item
    elif file_type == "world":
        world_name = 'world name="{}"'.format("rwc2018")

        sdf_dict[sdf_dict.keys()[0]] = {world_name: {}}
        sdf_dict_world_level = sdf_dict[sdf_dict.keys()[0]][sdf_dict[sdf_dict.keys()[0]].keys()[0]]

        for item in x['composition']:
            if item['type'] == 'room':
                # Rooms make use of 'areas' but there currently is no implementation of areas in SDF, this still needs
                # to be created somehow (Virtual volume???)
                pass
            else:
                # If it isn't a room, it should be a 'regular' model/object or a 'waypoint'. Both work through including
                # the associated model.sdf files with a pose in a model, so:
                model_name = 'model name ="{}"'.format(item['id'])
                sdf_dict_world_level[model_name] = {'pose': fill_pose(item),
                                                    'include': {'uri': 'model://{}/model.sdf'.format(item['type'])}}

    print "==============\nSDF Dictionary = " + str(sdf_dict)

    xml = dicttoxml.dicttoxml(sdf_dict, attr_type=False) # custom_root='sdf_version'  (no spaces)
    myfile = open("xmltest.xml", "w")
    myfile.write(xml)

    dom = parseString(xml)
    teststr = str(dom.toprettyxml())
    teststr = teststr.replace('"', '').replace("&quot;", '"').replace("key name=", "")\
        .replace("?xml version=1.0 ?", '?xml version="1.0" ?')
    print teststr


if __name__ == "__main__":
    sys.exit(main())