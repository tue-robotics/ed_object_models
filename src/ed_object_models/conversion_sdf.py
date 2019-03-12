from os import getenv, path
import glob
import re
import yaml
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
from subprocess import check_call
from collections import OrderedDict


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_model_path(model_name, ext="yaml"):
    """
    Checks for model file in ED_MODEL_PATH
    :param model_name: name of the model
    :type model_name: str
    :param ext: extension of the file: yaml/sdf
    :type ext: str
    :return: absolute model path or empty string
    :rtype: str
    """
    ed_model_path = getenv("ED_MODEL_PATH")
    if ext == "sdf":
        model_path = ed_model_path + "/{}/model*.{}".format(model_name, ext)
        files = glob.glob(model_path)
        if len(files) == 0:
            return ""
        return files[-1]

    else:
        model_path = ed_model_path + "/{}/model.{}".format(model_name, ext)
        if not path.isfile(model_path):
            return ""
        return model_path


def unique_name(name, names):
    """
    Provide a unique name based on name. If name already in names, the name is changed.
    If the name ends with digits, this number is increased. If the name doesn't end with a digit, the name is append
    with '1'. This continues until a unique name is found.
    :param name: name you want to be unique
    :type name: str
    :param names: list of names which are already used
    :type names: list
    :return: unique name
    :rtype: str
    """
    while name in names or not name:
        digits = re.search(r'\d+$', name)
        if name and digits:
            digits = digits.group()
            n_digits = len(digits)
            name = name[:-n_digits] + str(int(digits) + 1)
        else:
            name = name + str(1)
    names.append(name)
    return name


def read_pose(yaml_dict):
    """
    converts pose in yaml dict to string of 6 coordinates.
    :param yaml_dict: dict with possible pose as key on first level in dict
    :type yaml_dict: dict
    :return: string with 6 coordinates
    :rtype: str
    """
    pose = [0, 0, 0, 0, 0, 0]
    if "pose" in yaml_dict:
        # Check if coordinates are in pose, if so overwrite default 0
        options = {"x": 0, "y": 1, "z": 2, "rx": 3, "ry": 4, "rz": 5, "X": 3, "Y": 4, "Z": 5}
        for k, v in options.items():
            if k in yaml_dict["pose"]:
                pose[v] = yaml_dict["pose"][k]

    return " ".join(map(str, pose))


def read_geometry(shape_item, model_name):
    """
    Convert a shape item to a SDF geometry. With a possible pose offset. Which should be added to
    visual/collision/virtual_volume
    :param shape_item: dict with shape description
    :type shape_item: dict
    :param model_name: name of current model being converted
    :type model_name: str
    :return: tuple of geometry, link_pose and geometry_pose OR tuple of 3x None in case of error
    :rtype: tuple
    """
    geometry = {}
    link_pose = read_pose(shape_item)
    geometry_pose = None

    if "cylinder" in shape_item:
        yml_cylinder = shape_item["cylinder"]
        geometry["cylinder"] = {"radius": yml_cylinder["radius"], "length": yml_cylinder["height"]}
        if "pose" in yml_cylinder:
            link_pose = read_pose(yml_cylinder)

    elif "box" in shape_item:
        yml_box = shape_item["box"]
        if "size" in yml_box:
            yml_box_size = yml_box["size"]
            box_size_list = [yml_box_size["x"], yml_box_size["y"], yml_box_size["z"]]
            box_size = " ".join(map(str, box_size_list))
            geometry["box"] = {"size": box_size}
        elif "min" in yml_box:
            yml_box_min = yml_box["min"]
            yml_box_max = yml_box["max"]
            size_x = yml_box_max["x"] - yml_box_min["x"]
            size_y = yml_box_max["y"] - yml_box_min["y"]
            size_z = yml_box_max["z"] - yml_box_min["z"]
            box_size_list = [size_x, size_y, size_z]
            box_size = " ".join(map(str, box_size_list))

            pos_x = yml_box_min["x"] + float(size_x)/2
            pos_y = yml_box_min["y"] + float(size_y)/2
            pos_z = yml_box_min["z"] + float(size_z)/2
            box_pose_list = [pos_x, pos_y, pos_z, 0, 0, 0]
            geometry_pose = " ".join(map(str, box_pose_list))

            geometry["box"] = {"size": box_size}

        if "pose" in yml_box:
            link_pose = read_pose(yml_box)

    elif "path" in shape_item and "blockheight" in shape_item:

        # If there is a path and a blockheight in the shape_item, then there is a heightmap included in the yaml file
        model_folder = path.dirname(get_model_path(model_name))
        image_path = model_folder + "/{}".format(shape_item["path"])
        mesh_path = "{}.stl".format(path.splitext(image_path)[0])

        # Execute ImageMagick command to invert the image
        try:
            check_call("rosrun ed ed_heightmap_to_mesh {} {} {} {} {} {}".
                       format(image_path,
                              mesh_path,
                              shape_item["resolution"],
                              shape_item["blockheight"],
                              shape_item["origin_x"],
                              shape_item["origin_y"]),
                       executable="/bin/bash",
                       shell=True)
        except Exception as e:
            print(bcolors.FAIL + bcolors.BOLD + "[{}] ".format(model_name) + str(e) + bcolors.ENDC)
            raise

        sdf_mesh = {"uri": "model://{}/{}".format(model_name, path.relpath(mesh_path, model_folder))}
        geometry["mesh"] = sdf_mesh

    elif "path" in shape_item and ".xml" in shape_item["path"]:
        print(bcolors.WARNING +
              "[{}] Conversion of XML shapes is not implemented, please convert to yaml manually first"
              .format(model_name)
              + bcolors.ENDC)
        return None, None, None

    else:
        print(bcolors.FAIL + "[{}] No parsable shapes found".format(model_name) + bcolors.ENDC)
        return None, None, None

    return geometry, link_pose, geometry_pose


def read_shape_item(shape_item, link_names, color, model_name):
    """
    Convert shape item to a link with collision and visual elements
    :param shape_item: dict of one shape item
    :type shape_item: dict
    :param link_names: list of link names already used
    :type link_names: list
    :param color: None or dict of rgb values (0-1.0)
    :type color: dict
    :param model_name: name of current model being converted
    :type model_name: str
    :return: dict of SDF link element OR None in case of error
    :rtype: dict
    """
    sdf_link_item = {}

    # name
    name = ""
    if "#" in shape_item:
        name = shape_item["#"]
    # Unique name should be known here
    name = unique_name(name, link_names)
    sdf_link_item["name"] = name

    geometry, link_pose, geometry_pose = read_geometry(shape_item, model_name)

    if geometry is None:
        print(bcolors.FAIL + "[{}] Error during geometry parsing of shape:".format(model_name))
        print(str(shape_item) + bcolors.ENDC)
        return None

    # Maybe have a default name for collision and visual instead of link name
    sdf_link_item["collision"] = {"name": name, "geometry": geometry.copy()}
    # Copy to prevent textures in collision
    sdf_link_item["visual"] = {"name": name, "geometry": geometry.copy()}
    if geometry_pose:
        sdf_link_item["collision"]["pose"] = geometry_pose
        sdf_link_item["visual"]["pose"] = geometry_pose
    if color:
        color_str = " ".join(map(str, color.values()+[1]))
        sdf_link_item["visual"]["material"] = {"ambient": color_str}
    if "heightmap" in sdf_link_item["visual"]["geometry"]:
        sdf_link_item["visual"]["geometry"]["heightmap"]["texture"] = \
            {"diffuse": "file://media/materials/textures/grey.png",
             "normal": "file://media/materials/textures/normal.png",
             "size": 1}
        sdf_link_item["visual"]["geometry"]["heightmap"]["use_terrain_paging"] = "false"

    # pose
    sdf_link_item["pose"] = link_pose

    return sdf_link_item


def read_shape(shape, link_names, color, model_name):
    """
    Convert (array of) shape(s) to list of SDF links
    :param shape: shape dict
    :type shape: dict
    :param link_names: list of link names already used
    :type link_names: list
    :param color: None or dict of rgb values (0-1.0)
    :type color: dict
    :param model_name: name of current model being converted
    :type model_name: str
    :return: list of link elements OR None in case of error
    :rtype: list
    """
    sdf_link = []
    # Check if compound type has name (inserted as comment in yaml)
    if "compound" in shape:
        for item in shape["compound"]:
            shape_item = read_shape_item(item, link_names, color, model_name)
            if shape_item is None:
                print(bcolors.FAIL + "[{}] Error during compound shape parsing".format(model_name) + bcolors.ENDC)
                return None
            sdf_link.append(shape_item)
    else:
        shape_item = read_shape_item(shape, link_names, color, model_name)
        if shape_item is None:
            print(bcolors.FAIL + "[{}] Error during single shape parsing".format(model_name) + bcolors.ENDC)
            return None
        sdf_link.append(shape_item)

    return sdf_link


def read_areas(areas, link_names, model_name):
    """
    Convert areas to links with a virtual area
    :param areas: list of areas
    :type areas: list
    :param link_names: list of link names already used
    :type link_names: list
    :param model_name: name of current model being converted
    :type model_name: str
    :return: list of links with a virtual area child element OR None in case of error
    :rtype: list
    """
    sdf_link = []
    if not isinstance(areas, list):
        print("areas should be a list")
        return sdf_link

    area_names = []
    for area in areas:
        name = area["name"]
        if name == "near":
            continue

        uname = unique_name(name, link_names)
        if not uname == name:
            print(bcolors.BOLD + "Name of area has changed from '{}' to '{}'".format(name, uname) + bcolors.ENDC)
        sdf_link_item = {"name": uname}

        for shape_item in area["shape"]:
            geometry, link_pose, geometry_pose = read_geometry(shape_item, model_name)
            if geometry is None:
                print(bcolors.FAIL + "[{}] Error during geometry parsing of area: {}".format(model_name, uname)
                      + bcolors.ENDC)
                return None
            shape_name = unique_name(uname, area_names)
            sdf_link_item["virtual_volume"] = {"name": shape_name, "geometry": geometry}
            if geometry_pose:
                sdf_link_item["virtual_volume"]["pose"] = geometry_pose

            sdf_link.append(sdf_link_item)

    return sdf_link


def parse_to_xml(xml, item, list_name=""):
    """
    Extend XML with elements from a dict, list or a string
    :param xml: xml element
    :type xml: xml.etree.ElementTree.Element
    :param item: dict, list or str
    :type item: dict or list or str
    :param list_name: name of list, needs to be passed on by parent for each element
    :type list_name: str
    :raises: Exception: incorrect usage of argument or unknown class type
    """
    if isinstance(item, list):
        if not list_name:
            raise Exception(bcolors.FAIL + "(parse_to_xml) list_name should be passed on by parent in case of a list"
                            + bcolors.ENDC)
        for v in item:
            child = ET.SubElement(xml, list_name)
            parse_to_xml(child, v)
    elif isinstance(item, dict):
        for k, v in item.items():
            # attributes
            if k == "name" or k == "version" or k == "type":
                xml.set(k, v)

                # Names in includes are elements, not attributes. Using below code generates names as attributes AND as
                # elements:
                if not k == "name":
                    continue

                # Another solution to above would be to input an extra argument to the parse_to_xml function to check if
                # the file that is parsed is a world or a model. For models the names can then be set as attributes, for
                # worlds as elements.

            if isinstance(v, list):
                parse_to_xml(xml, v, k)
            else:
                child = ET.SubElement(xml, k)
                parse_to_xml(child, v)
    elif isinstance(item, str) or isinstance(item, float) or isinstance(item, int):
        xml.text = str(item)
    else:
        raise Exception(bcolors.WARNING + "(parse_to_xml) Cannot not parse object type: '{}'".format(type(item))
                        + bcolors.ENDC)


def write_xml_to_file(xml_element, path):
    """
    write xml element to a file
    :param xml_element: xml element
    :type xml_element: xml.etree.ElementTree.Element
    :param path: full path of file, which to write
    :type path: str
    """
    # generate xml string with indentation
    xml_dom = parseString(ET.tostring(xml_element, encoding="utf-8"))
    pretty_xml_string = xml_dom.toprettyxml(indent="  ")

    with open(path, "w") as f:
        f.write(pretty_xml_string)


def convert_world(yml, model_name, recursive=False):
    """
    convert world yaml to sdf world dict
    :param yml: yaml object of a world ed yaml
    :type yml: dict
    :param model_name: Name of the world
    :type model_name: str
    :param recursive: If true all included models are also converted
    :type recursive: bool
    :return: sdf dict of the model
    :rtype: dict
    """
    light = {"type": "directional", "name": "sun",
             "cast_shadows": "true", "pose": "0 0 10 0 0 0", "diffuse": "0.8 0.8 0.8 1",
             "specular": "0.2 0.2 0.2 1", "direction": "0.5 0.1 -0.9",
             "attenuation": {"range": 1000, "constant": 0.9, "linear": 0.01, "quadratic": 0.001}}
    physics = {"type": "ode", "real_time_update_rate": 400.0, "max_step_size": 0.0025,
               "ode": {"solver": {"type": "quick", "iters": 100}, "constraints": {"cfm": 0.0001}}}
    world = {"name": model_name, "include": [], "model": [], "light": light, "physics": physics}

    world_include = world["include"]
    world_model = world["model"]
    if not isinstance(yml["composition"], list):
        print(bcolors.FAIL + bcolors.BOLD + "[{}] composition should be a list".format(model_name) + bcolors.ENDC)
        return 1
    for item in yml["composition"]:
        if not isinstance(item, dict):
            print(bcolors.FAIL + bcolors.BOLD + "[{}] Items in composition should be a dict".format(model_name)
                  + bcolors.ENDC)
            return 1
        include = {"name": item["id"]}
        if "type" in item:
            if recursive:
                # Todo: If there are multiple objects of the same type, then this type's SDF is created for every
                #       instance of the type (for instance ids: table1 and table2 are both type TableA, so it will
                #       recreate the SDF and config for TableA twice)
                main(item["type"], recursive=recursive)
            if item["type"] in ["room", "waypoint"]:
                model = convert_model(item, item["id"])
                model["pose"] = read_pose(item)
                model["type"] = item["type"]
                world_model.append(model)
            else:
                include["uri"] = "model://{}".format(item["type"])
                include["pose"] = read_pose(item)
                world_include.append(include)
        else:
            model = convert_model(item, item["id"])
            model["pose"] = read_pose(item)
            world_model.append(model)

    return world


def convert_model(yml, model_name):
    """
    convert model yaml to sdf model dict
    :param yml: yaml object of a world ed yaml
    :type yml: dict
    :param model_name: Name of the model
    :type model_name: str
    :return: sdf dict of the model
    :rtype: dict
    """
    model = {"name": model_name, "static": "true", "link": []}  # All default parameters should be added here
    color = OrderedDict()
    if "color" in yml:
        color["red"] = yml["color"]["red"]
        color["green"] = yml["color"]["green"]
        color["blue"] = yml["color"]["blue"]

    link_names = []
    if "shape" in yml:
        shape = read_shape(yml["shape"], link_names, color, model_name)
        if shape is None:
            print(bcolors.FAIL + bcolors.BOLD + "[{}] Error during shape parsing".format(model_name) + bcolors.ENDC)
            return 1
        model["link"].extend(shape)

    if "areas" in yml:
        areas = read_areas(yml["areas"], link_names, model_name)
        if areas is None:
            print(bcolors.FAIL + bcolors.BOLD + "[{}] Error during areas parsing".format(model_name) + bcolors.ENDC)
            return 1
        model["link"].extend(areas)

    return model


def main(model_name, recursive=False):
    """
    Main conversion script
    :param model_name: Name of the model, model_name/model.yaml should exist in ED_MODEL_PATH
    :type model_name: str
    :param recursive: If true all included models are also converted
    :type recursive: bool
    :return: Good: 0, Error: 1
    :rtype: int
    """
    # strip trailing slash
    if model_name[-1] == "/":
        model_name = model_name[:-1]
    # get model path
    yaml_model_path = get_model_path(model_name, "yaml")
    if not yaml_model_path:
        print (bcolors.FAIL + bcolors.BOLD + "[{}] No model path found".format(yaml_model_path) + bcolors.ENDC)
        return 1

    # declare sdf dict including sdf version
    sdf_version = 1.6
    sdf = {"version": str(sdf_version)}

    # read yaml file
    with open(yaml_model_path, "r") as stream:
        try:
            yml = yaml.load(stream)
        except yaml.YAMLError as e:
            raise e

    # determine file_type
    if "composition" in yml:
        sdf["world"] = convert_world(yml, model_name, recursive)
    else:
        sdf["model"] = convert_model(yml, model_name)

    # convert combination of dicts and lists to ET Elements
    xml = ET.Element("sdf")
    try:
        parse_to_xml(xml, sdf)
    except Exception as e:
        print(bcolors.FAIL + bcolors.BOLD + "[{}] (XML) ".format(model_name) + str(e) + bcolors.ENDC)
        return 1

    # write to sdf file
    sdf_filename = "model.sdf"
    model_sdf_path = path.join(path.dirname(yaml_model_path), sdf_filename)
    write_xml_to_file(xml, model_sdf_path)

    ##
    # Generate model.config
    model_config_path = path.join(path.dirname(yaml_model_path), "model.config")
    if path.isfile(model_config_path):
        with open(model_config_path, "r") as f:
            config_string = "".join(line.strip() for line in f)

        config_root = ET.fromstring(config_string)

        # set name and description
        config_sdfs = config_root.findall("sdf")
        if all([config_sdf.attrib['version'] != str(sdf_version) for config_sdf in config_sdfs]):
                config_sdf.text = sdf_filename
    else:
        test_model_path = get_model_path("test_sdf", "sdf")
        if not test_model_path:
            print(bcolors.FAIL + bcolors.BOLD + "Can't find 'test_sdf' model."
                                                "Which is used for generation of 'model.config'")
            print("model.config not generated. Gazebo will not be able to find the model: '{}'".format(model_name)
                  + bcolors.ENDC)
            return 1

        test_config_path = path.join(path.dirname(test_model_path), "model.config")
        if not path.exists(test_config_path):
            print(bcolors.FAIL + bcolors.BOLD + "model.config path: '{}' doesn't exist".format(test_config_path))
            print("model.config not generated. Gazebo will not be able to find the model: '{}'".format(model_name)
                  + bcolors.ENDC)
            return 1

            # xml parsing doesn't ignore whitespace, so reading the file manually
        with open(test_config_path, "r") as f:
            config_string = "".join(line.strip() for line in f)

        config_root = ET.fromstring(config_string)

        # set name and description
        config_root.find("name").text = model_name
        config_root.find("description").text = model_name
        config_sdf = config_root.find("sdf")
        config_sdf.attrib['version'] = str(sdf_version)
        config_sdf.text = sdf_filename

        # write model.config
        write_xml_to_file(config_root, model_config_path)

    print(bcolors.OKGREEN + "[{}] Successfully converted to SDF".format(model_name) + bcolors.ENDC)
    return 0
