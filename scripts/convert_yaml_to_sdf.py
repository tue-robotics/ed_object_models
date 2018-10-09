#!/usr/bin/env python

import sys
import yaml
import dicttoxml


# if len(sys.argv) <= 1:
#     print "Please provide a file as input"
#     sys.exit(1)

# First determine type of model.yaml: "world
# Raw input can be replaced by fancier read_option in create-model.py
# file_type = raw_input("File type ('room' or 'object'): ")
# model_name = raw_input("Model name: ")

file_type = "object"
model = {'sdf version="1.6"': {}}
print model.keys()[0]

with open("model.yaml", 'r') as stream:
        try:
                    x = yaml.load(stream)
                            # print(x)
                                except yaml.YAMLError as exc:
                                            print(exc)

                                            # test = {'sdf version="1.6"': {'model name = "couch"': {'pose': [0, 0, 0.5, 0, 0, 0], 'static': 'false'}}}
                                            #
                                            # xml = dicttoxml.dicttoxml(test)
                                            # myfile = open("xmltest.xml", "w")
                                            # myfile.write(xml)

                                            print(x)
                                            if isinstance(x,dict):
                                                    for key in x:
                                                                if file_type == "object":
                                                                                print "Dictionary item:", key

                                                                            elif isinstance(x,list):
                                                                                    for item in x:
                                                                                                print 'List item:', item

