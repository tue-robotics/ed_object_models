#! /usr/bin/python

from __future__ import print_function

import sys
import yaml
import os

ROOT = os.environ['ED_MODEL_PATH']
DEFAULT_BOTTOM_CLEARANCE = 0.02  # The 'onTopOff' area will start DEFAULT_BOTTOM_CLEARANCE above an object
DEFAULT_SIDE_CLEARANCE = 0.03  # The 'onTopOff' area will be DEFAULT_SIDE_CLEARANCE smaller than an object in side dir
DEFAULT_FRONT_CLEARANCE = 0.01  # The 'onTopOff' area will be DEFAULT_SIDE_CLEARANCE smaller than an object in front
DEFAULT_BACK_CLEARANCE = 0.01  # The 'onTopOff' area will be DEFAULT_SIDE_CLEARANCE smaller than an object in back
ON_TOP_OFF_HEIGHT = 0.25  # Height of an 'onTopOff' box
DEFAULT_IN_FRONT_SIDE_CLEARANCE = 0.1  # The 'inFrontOf' area will be DEFAULT_IN_FRONT_SIDE_CLEARANCE smaller on each side
DEFAULT_IN_FRONT_DISTANCE = 0.4  # Distance from object to start 'inFrontOf' area
DEFAULT_IN_FRONT_SIZE = 0.2  # Size of 'inFrontOf' area
ROUND_LEVEL = 4  # Level of rounding


# ----------------------------------------------------------------------------------------------------

def read_option(message, options=[], default=None, help=None):
    """
    Reads a option from input from a list of options, with message, default option and help message.
    :param message: Message to be printed before asking for input
    :type message: str
    :param options: options in which input should be
    :type options: list
    :param default: Default option
    :type default: depending on the options
    :param help: Help message to be printed
    :type help: str
    :return: no return
    """
    while True:
        option = raw_input(message)
        if option:
            if option == "?":
                if help:
                    print(help)
                print("Possible options: {}".format(options))
            elif options and option in options:
                return option
            elif not options:
                return option
            else:
                print("Unknown option. Options are: {}".format(options))
        elif not option:
            if default:
                return default
            else:
                print("Please specify an option")


def read_float(message, default=None, help=None):
    """
    Reads a float from input, with message, default option and help message.
    :param message: Message to be printed before asking for input
    :type message: str
    :param default: Default option
    :type default: float
    :param help: Help message to be printed
    :type help: str
    :return: no return
    """
    while True:
        option = raw_input(message)
        if not option:
            if default is not None:
                return default
            else:
                print("Please provide a value.")
        elif option == "?":
            if help:
                print(help)
            else:
                print("Please provide a number")
        else:
            try:
                return float(option)
            except ValueError:
                print("Expected a number.")
                pass


# ----------------------------------------------------------------------------------------------------
class ShapeCreator:

    def __init__(self, room, model_name):
        folderpath = os.path.join(ROOT, room, model_name)
        filepath = os.path.join(folderpath, 'model.yaml')
        if os.path.exists(filepath):
            print("Model name already used in this room")
            sys.exit()
        if not os.path.exists(folderpath):
            os.makedirs(folderpath)
        else:
            print("""
            Folder name is already used, no model found. Keep directory clean!
            Continue with creating your model""")

        self.f = open(filepath, "w")

        self.data = {'shape': {'compound': []},
                     'areas': []}

    def write(self):
        """
        writing the dict in self.data to the yaml file.
        :return: no return
        """
        self.f.write(yaml.safe_dump(self.data, default_flow_style=False, indent=4))

    # def set_type(self, t):
    #     """
    #     Sets the type of the model
    #     :param t: the type of the model
    #     :type t: str
    #     """
    #     self.data['type'] = t

    def add_box(self, l, w, h, x, y, z, comment=""):
        """
        add a box to the shape
        :param l: depth
        :type l: double
        :param w: width
        :type w: double
        :param h: height
        :type h: double
        :param x: relative position in x
        :type x: double
        :param y: relative position in y
        :type y: double
        :param z: relative position in z
        :type z: double
        :param comment: name of the box
        :type comment: str
        :return: no return
        """
        self.data['shape']['compound'].append({'box': {'#': comment, 'pose': {'x': x, 'y': y, 'z': z},
                                                       'size': {'x': l, 'y': w, 'z': h}}})

    def add_area(self, name, area_type, data):
        """
        add an area to an object
        :param name: name of the area, e.g. offset, shape
        :param area_type: str
        :param data: data of the area
        :param data: dict/list
        :return: no return
        """
        self.data['areas'].append({'name': name,
                                  area_type: data})

    def add_in_front_of(self, depth, width, side_clearance=DEFAULT_IN_FRONT_SIDE_CLEARANCE,
                        distance=DEFAULT_IN_FRONT_DISTANCE,
                        size=DEFAULT_IN_FRONT_SIZE):
        """
        add an 'in_front_of' area to an object. It takes into account the size of the object
        :param depth: depth of the object
        :type depth: double
        :param width: width of the object
        :type width: double
        :param side_clearance: The area will be this much smaller on each side than the object
        :type side_clearance: double
        :param distance: distance between object and area
        :type distance: double
        :param size: depth of the area
        :type size: double
        :return: no return
        """

        boxmin = {'x': round(depth/2 + distance, ROUND_LEVEL),
                  'y': round(-width/2 + side_clearance, ROUND_LEVEL),
                  'z': 0.0}
        boxmax = {'x': round(depth/2 + distance+size, ROUND_LEVEL),
                  'y': round(width/2 - side_clearance, ROUND_LEVEL),
                  'z': 0.01}

        self.add_area("in_front_of", "shape", [{'box': {'min': boxmin, 'max': boxmax}}])

    def add_on_top_of(self, name="", bottom_clearance=DEFAULT_BOTTOM_CLEARANCE,
                      side_clearance=DEFAULT_SIDE_CLEARANCE, front_clearence=DEFAULT_FRONT_CLEARANCE,
                      back_clearence=DEFAULT_BACK_CLEARANCE, height=ON_TOP_OFF_HEIGHT):
        """ Adds an on_top_off_area to the model. This must be called right after the element w.r.t.
        which the on_top_off is specified (e.g., the table top) has been added.
        :param name: name of the area
        :type name: str
        :param bottom_clearance: the clearance between the model and the on_top_off box
        :type bottom_clearance: double
        :param side_clearance: the clearance between the sides of the model and the on_top_off_box
        :type side_clearance: double
        :param front_clearence: the clearance between the front of the model and the on_top_off_box
        :type front_clearence: double
        :param back_clearence: the clearance between the back of the model and the on_top_off_box
        :type back_clearence: double
        :param height: the height of the box
        :type height: double
        :return: no return
        """

        if not name:
            name = 'on_top_of'
        if len(self.data['shape']['compound']) == 0:
            print("No shapes yet, cannot add ontopoff")
            return
        else:
            shape = self.data['shape']['compound'][-1]
        if 'box' not in shape:
            print("No box in this shape, cannot add ontopoff")
            return

        pose = shape['box']['pose']
        size = shape['box']['size']

        boxmin = {'x': round(pose['x'] - size['x']/2.0 + back_clearence, ROUND_LEVEL),
                  'y': round(pose['y'] - size['y']/2.0 + side_clearance, ROUND_LEVEL),
                  'z': round(pose['z'] + size['z']/2.0 + bottom_clearance, ROUND_LEVEL)}
        boxmax = {'x': round(pose['x'] + size['x']/2.0 - front_clearence, ROUND_LEVEL),
                  'y': round(pose['y'] + size['y']/2.0 - side_clearance, ROUND_LEVEL),
                  'z': round(pose['z'] + size['z']/2.0 + bottom_clearance + height, ROUND_LEVEL)}

        self.add_area(name, "shape", [{'box': {'min': boxmin, 'max': boxmax}}])

    def add_near(self, offset=0.7):
        """
        Adds an 'near' area to the model with given offset
        :param offset: the offset w.r.t. the model edges
        :type offset: double
        :return: no return
        """
        self.add_area("near", "offset", offset)


# ----------------------------------------------------------------------------------------------------
def main():

    print("")
    print("""Answer the questions given. If you do not understand, give '?' as input.
A 'model.yaml' file will be created which can be used as ED model.
All lengths / distances are in meters, unless specified otherwise.""")
    print("")

    room = read_option("Room: ")
    model_type = read_option("Model type: ", ["table", "cabinet", "box"])
    model_name = read_option("Model name: ")

    s = ShapeCreator(room, model_name)
    # s.set_type(model_type)
    s.add_near()

    if model_type == "table":

        print("")
        height = read_float("Height: ", help="Distance from ground to top of the table [m]")
        length = read_float("Length: ", help="Table length [m]")
        width  = read_float("Width:  ", help="Table width [m]")

        print("")
        table_top_thickness = read_float("Table top thickness [m]: ")

        print("")
        lt = read_float("Leg thickness: ", help="We assume square legs. How wide / thick are the legs?")
        lx_offset = read_float("Optional: Leg offset (length) [m]: ", 0,
            help="(Optional) How far are the legs places inwards w.r.t. the table top (in the length direction)")
        ly_offset = read_float("Optional: Leg offset (width) [m]:  ", lx_offset,
            help="(Optional) How far are the legs places inwards w.r.t. the table top (in the width direction)")

        s.add_box(length, width, table_top_thickness, 0, 0, round(height - table_top_thickness / 2, ROUND_LEVEL),
                  "Table top")
        s.add_on_top_of()

        lx = round((length - lt) / 2 - lx_offset, ROUND_LEVEL)
        ly = round((width  - lt) / 2 - ly_offset, ROUND_LEVEL)
        lh = round(height - table_top_thickness, ROUND_LEVEL)
        lz = round(lh / 2, ROUND_LEVEL)

        s.add_box(lt, lt, lh, -lx, -ly, lz, "Leg")
        s.add_box(lt, lt, lh,  lx, -ly, lz, "Leg")
        s.add_box(lt, lt, lh, -lx,  ly, lz, "Leg")
        s.add_box(lt, lt, lh,  lx,  ly, lz, "Leg")
        s.add_in_front_of(length, width)

    elif model_type == "box":

        print("")
        height = read_float("Height [m]: ", help="Distance from ground to top of the box object")
        width  = read_float("Width [m]: ",  help="Box width")
        depth  = read_float("Depth [m]: ",  help="Box depth")

        s.add_box(depth, width, height, 0, 0, round(height / 2, 3), "Main object")
        s.add_on_top_of()
        s.add_in_front_of(depth, width)

    elif model_type == "cabinet":

        print("")
        height = read_float("Height [m]: ", help="Distance from ground to top of the cabinet (including frame)")
        width  = read_float("Width [m]:  ", help="Cabinet width (including frame)")
        depth  = read_float("Depth [m]:  ", help="Cabinet depth (including frame)")
        thickness = read_float("Frame thickness: ", help="How thick are the panels that define the cabinet frame (not the shelves)?")
        top_thickness = read_float("Top Frame thickness: ", help="Thickness of the top of the cabinet frame")

        print("")
        shelf_heights = []
        while True:
            shelf_height = read_float("Shelf %s, height [m]: " % (len(shelf_heights) + 1), -1,
                help="Distance from ground to bottom of shelf. Leave empty if all shelves have been entered")
            if shelf_height == -1:
                break
            shelf_heights += [shelf_height]

        shelf_thickness = shelf_heights[:]
        for shelf_i in range(0, len(shelf_thickness)):
            shelf_thickness[shelf_i] = read_float("Thickness of shelf %s: " %(shelf_i+1))

        verticals = []
        while True:
            print("Enter distance from left side of the cabinet to the left side of the vertical")
            vertical = read_float("Position of vertical %s: " % (len(verticals) + 1), -1,
                                  help="Distance from left side of the cabinet to the left side of the vertical."
                                  "Leave empty is all verticals have been entered")
            if vertical == -1:
                break
            verticals += [vertical]

        vertical_thickness = verticals[:]
        for vertical_i in range(0, len(vertical_thickness)):
            vertical_thickness[vertical_i] = read_float("Thickness of vertical %s: " % (vertical_i+1))

        s.add_box(depth, thickness, height, 0, round(-(width - thickness) / 2, ROUND_LEVEL),
                  round(height / 2, ROUND_LEVEL), "Left side")
        s.add_box(depth, thickness, height, 0, round((width - thickness) / 2, ROUND_LEVEL),
                  round(height / 2, ROUND_LEVEL), "Right side")
        s.add_box(thickness, width, height,  round(-(depth - thickness) / 2, ROUND_LEVEL), 0,
                  round(height / 2, ROUND_LEVEL), "Back side")
        s.add_in_front_of(depth, width)

        pl_depth = round(depth - thickness, ROUND_LEVEL)
        pl_width = round((width - (thickness * 2)), ROUND_LEVEL)
        pl_height = round(height - thickness-shelf_heights[0]-shelf_thickness[0], ROUND_LEVEL)
        pl_x = round((thickness / 2), ROUND_LEVEL)

        s.add_box(pl_depth, pl_width, top_thickness, pl_x, 0, round(height - (top_thickness / 2), ROUND_LEVEL), "Top")

        for shelf_i in range(0, len(shelf_heights)):
            s.add_box(pl_depth, pl_width, shelf_thickness[shelf_i], pl_x, 0,
                      round(shelf_heights[shelf_i] + (shelf_thickness[shelf_i] / 2), ROUND_LEVEL),
                      "Shelf %s" % (shelf_i+1))
            if not verticals:
                s.add_on_top_of("shelf%s" % (shelf_i+1))
        for vertical_i in range(0, len(verticals)):
            s.add_box(pl_depth, vertical_thickness[vertical_i], pl_height, pl_x,
                      round(-width / 2 + verticals[vertical_i] + vertical_thickness[vertical_i] / 2, ROUND_LEVEL),
                      round(shelf_thickness[0]+(pl_height / 2), ROUND_LEVEL), "vertical %s" % (vertical_i+1))

    s.write()


if __name__ == "__main__":
    sys.exit(main())
