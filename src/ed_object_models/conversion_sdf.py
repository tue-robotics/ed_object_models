from typing import List, Tuple, Union

from os import getenv, path, rename, pathsep, makedirs
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


def get_model_path(model_name: str, ext: str = "yaml") -> str:
    """
    Checks for model file in ED_MODEL_PATH

    :param model_name: name of the model
    :param ext: extension of the file: yaml/sdf
    :return: absolute model path or empty string if not found
    """
    ed_model_paths = getenv("ED_MODEL_PATH").split(pathsep)
    if ext == "sdf":
        for ed_model_path in ed_model_paths:
            model_path = ed_model_path + "/{}/model*.{}".format(model_name, ext)
            files = glob.glob(model_path)
            if len(files) != 0:
                return files[-1]

    else:
        for ed_model_path in ed_model_paths:
            model_path = ed_model_path + "/{}/model.{}".format(model_name, ext)
            if path.isfile(model_path):
                return model_path

    return ""


def unique_name(name: str, names: List[str]) -> str:
    """
    Provide a unique name based on name. If name already in names, the name is changed.
    If the name ends with digits, this number is increased. If the name doesn't end with a digit, the name is append
    with '1'. This continues until a unique name is found.

    :param name: name you want to be unique
    :param names: list of names which are already used
    :return: unique name
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


def read_pose(yaml_dict: dict) -> str:
    """
    converts pose in yaml dict to string of 6 coordinates.

    :param yaml_dict: dict with possible pose as key on first level in dict
    :return: string with 6 coordinates
    """
    pose = [0, 0, 0, 0, 0, 0]
    if "pose" in yaml_dict:
        # Check if coordinates are in pose, if so overwrite default 0
        options = {"x": 0, "y": 1, "z": 2, "rx": 3, "ry": 4, "rz": 5, "X": 3, "Y": 4, "Z": 5}
        for k, v in options.items():
            if k in yaml_dict["pose"]:
                pose[v] = yaml_dict["pose"][k]

    return " ".join(map(str, pose))


def read_geometry(shape_item: dict, model_name: str) -> Union[Tuple[dict, str, str], Tuple[None, None, None]]:
    """
    Convert a shape item to a SDF geometry. With a possible pose offset. Which should be added to
    visual/collision/virtual_volume

    :param shape_item: dict with shape description
    :param model_name: name of current model being converted
    :return: tuple of geometry, link_pose and geometry_pose OR tuple of 3x None in case of error
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

    elif "polygon" in shape_item:
        yml_polygon = shape_item["polygon"]
        points = []
        for point in yml_polygon["points"]:
            point = OrderedDict(sorted(point.items()))
            points.append(" ".join(map(str, point.values())))
        geometry["polyline"] = {"point": points,
                                "height": yml_polygon["height"]}

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


def read_shape_item(shape_item: dict, link_names: List[str], color: OrderedDict, model_name: str) -> Union[dict, None]:
    """
    Convert shape item to a link with collision and visual elements

    :param shape_item: dict of one shape item
    :param link_names: list of link names already used
    :param color: None or dict of rgb values (0-1.0)
    :param model_name: name of current model being converted
    :return: dict of SDF link element OR None in case of error
    """
    sdf_link_item = {}

    # name
    name = ""
    if "#" in shape_item:
        name = shape_item["#"]
    # Unique name should be known here
    name = unique_name(name, link_names)
    sdf_link_item["name"] = f"{name}_link"

    geometry, link_pose, geometry_pose = read_geometry(shape_item, model_name)

    if geometry is None:
        print(bcolors.FAIL + "[{}] Error during geometry parsing of shape:".format(model_name))
        print(str(shape_item) + bcolors.ENDC)
        return None

    # Maybe have a default name for collision and visual instead of link name
    sdf_link_item["collision"] = {"name": f"{name}_col", "geometry": geometry.copy()}
    # Copy to prevent textures in collision
    sdf_link_item["visual"] = {"name": f"{name}_vis", "geometry": geometry.copy()}
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


def read_shape(shape: dict, link_names: List[str], color: OrderedDict, model_name: str) -> Union[List, None]:
    """
    Convert (array of) shape(s) to list of SDF links

    :param shape: shape dict
    :param link_names: list of link names already used
    :param color: None or dict of rgb values (0-1.0)
    :param model_name: name of current model being converted
    :return: list of link elements OR None in case of error
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


def read_areas(areas: List, link_names: List[str], model_name: str) -> Union[List, None]:
    """
    Convert areas to links with a virtual area

    :param areas: list of areas
    :param link_names: list of link names already used
    :param model_name: name of current model being converted
    :return: list of links with a virtual area child element OR None in case of error
    """
    sdf_link = []
    if not isinstance(areas, list):
        print(bcolors.FAIL + "[{}] Areas should be a list".format(model_name) + bcolors.ENDC)
        return None

    area_names = []
    for area in areas:
        name = area["name"]
        if name == "near":
            continue

        uname = unique_name(name, link_names)
        if not uname == name:
            print(bcolors.BOLD + "Name of area has changed from '{}' to '{}'".format(name, uname) + bcolors.ENDC)
        sdf_link_item = {"name": f"{uname}_link"}

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


def parse_to_xml(xml: ET.Element, item: Union[list, dict, str, float, int], list_name: str = "") -> None:
    """
    Extend XML with elements from a dict, list or a string.
    This takes SDF attribute/element rules into account

    :param xml: xml element
    :param item: dict, list or str
    :param list_name: name of list, needs to be passed on by parent for each element
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
            attributes = ["version", "type"]  # children that are XML attributes in all SDF elements
            if xml.tag != "include":
                attributes.append("name")  # In 'include' name is a child element, in other elements it is an attribute

            if k in attributes:  # Write child as attribute
                xml.set(k, v)
                continue

            if isinstance(v, list):  # Write child list
                parse_to_xml(xml, v, k)
            else:  # Write child as element
                child = ET.SubElement(xml, k)
                parse_to_xml(child, v)
    elif isinstance(item, str) or isinstance(item, float) or isinstance(item, int):
        xml.text = str(item)
    else:
        raise Exception(bcolors.WARNING + "(parse_to_xml) Cannot not parse object type: '{}'".format(type(item))
                        + bcolors.ENDC)


def write_xml_to_file(xml_element: ET.Element, filepath: str) -> None:
    """
    Write xml element to a file

    :param xml_element: xml element
    :param filepath: full path of file, which to write
    """
    # generate xml string with indentation
    xml_dom = parseString(ET.tostring(xml_element, encoding="utf-8"))
    pretty_xml_string = xml_dom.toprettyxml(indent="  ")

    dirpath = path.dirname(filepath)
    if not path.isdir(dirpath):
        makedirs(dirpath)

    with open(filepath, "w") as f:
        f.write(pretty_xml_string)


def convert_world(yml: dict, model_name: str, recursive: bool = False) -> dict:
    """
    Convert world yaml to sdf world dict

    :param yml: yaml object of a world ed yaml
    :param model_name: Name of the world
    :param recursive: If true all included models are also converted
    :return: sdf dict of the model
    """
    light = {"type": "directional", "name": "sun",
             "cast_shadows": "true", "pose": "0 0 10 0 0 0", "diffuse": "0.8 0.8 0.8 1",
             "specular": "0.2 0.2 0.2 1", "direction": "0.5 0.1 -0.9",
             "attenuation": {"range": 1000, "constant": 0.9, "linear": 0.01, "quadratic": 0.001}}
    physics = {"type": "ode", "real_time_update_rate": 333.0, "max_step_size": 0.003,
               "ode": {"solver": {"type": "quick", "iters": 100}, "constraints": {"cfm": 0.0001}}}
    world = {"name": model_name, "include": [], "model": [], "light": light, "physics": physics}

    world_include = world["include"]
    world_model = world["model"]
    if not isinstance(yml["composition"], list):
        raise Exception(bcolors.FAIL + bcolors.BOLD + "[{}] composition should be a list".format(model_name)
                        + bcolors.ENDC)
    for item in yml["composition"]:
        if not isinstance(item, dict):
            raise Exception(bcolors.FAIL + bcolors.BOLD +
                            "[{}] Items in composition should be a dict".format(model_name) + bcolors.ENDC)
        include = {"name": item["id"]}
        if "type" in item:
            if recursive:
                # Todo: If there are multiple objects of the same type, then this type's SDF is created for every
                #       instance of the type (for instance ids: table1 and table2 are both type TableA, so it will
                #       recreate the SDF and config for TableA twice)
                convert_model_name(item["type"], recursive=recursive)
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


def convert_model(yml: dict, model_name: str) -> dict:
    """
    Convert model yaml to sdf model dict

    :param yml: yaml object of a world ed yaml
    :param model_name: Name of the model
    :return: sdf dict of the model
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
            raise Exception(bcolors.FAIL + bcolors.BOLD + "[{}] Error during shape parsing".format(model_name)
                            + bcolors.ENDC)
        model["link"].extend(shape)

    if "areas" in yml:
        areas = read_areas(yml["areas"], link_names, model_name)
        if areas is None:
            raise Exception(bcolors.FAIL + bcolors.BOLD + "[{}] Error during areas parsing".format(model_name)
                            + bcolors.ENDC)
        model["link"].extend(areas)

    return model


def convert_model_data(model_data: Union[dict, list], model_name: str, model_dir: str, recursive: bool = False) -> int:
    """
    Convert model data to SDF with the name 'model_name' in directory 'model_dir'.
    Most of the times model_dir=ROOT/model_name for a ROOT in ED_MODEL_PATH

    :param model_data: yaml data of the model
    :param model_name: Name of the model
    :param model_dir: Directory of the model.
    :param recursive: If true all included models are also converted
    :return: Good: 0, Error: 1
    """
    # declare sdf dict including sdf version
    sdf_version = 1.7
    sdf = {"version": str(sdf_version)}

    # determine file_type
    try:
        if "composition" in model_data:
            sdf["world"] = convert_world(model_data, model_name, recursive)
        else:
            sdf["model"] = convert_model(model_data, model_name)
    except Exception as e:
        print(bcolors.FAIL + bcolors.BOLD + "[{}] (CONVERSION) ".format(model_name) + str(e) + bcolors.ENDC)
        return 1

    # convert combination of dicts and lists to ET Elements
    xml = ET.Element("sdf")
    try:
        parse_to_xml(xml, sdf)
    except Exception as e:
        print(bcolors.FAIL + bcolors.BOLD + "[{}] (XML) ".format(model_name) + str(e) + bcolors.ENDC)
        return 1

    # write to sdf file
    sdf_filename = "model.sdf"
    sdf_model_path = path.join(model_dir, sdf_filename)

    ##
    # Generate model.config
    model_config_path = path.join(model_dir, "model.config")
    if path.isfile(model_config_path):  # SDF model already exist, edit model.config and rename sdf files if needed
        with open(model_config_path, "r") as f:
            config_string = "".join(line.strip() for line in f)

        config_root = ET.fromstring(config_string)

        # set name and description
        config_sdfs = config_root.findall("sdf")
        # if all([config_sdf.attrib['version'] != str(sdf_version) for config_sdf in config_sdfs]):
        #         config_sdf.text = sdf_filename
        newest_sdf = sorted(config_sdfs, key=lambda x: x.attrib['version'], reverse=True)[0]
        newest_sdf_version = float(newest_sdf.attrib['version'])
        if sdf_version > newest_sdf_version:  # Converting a newer version
            if newest_sdf.text == sdf_filename:   # Rename current newest version, if the same
                newest_sdf_filename = "model-{}.sdf".format(str(newest_sdf_version).replace('.', '_'))
                rename(sdf_model_path, path.join(model_dir, newest_sdf_filename))
                newest_sdf.text = newest_sdf_filename
            new_sdf = ET.Element("sdf")
            config_root.insert(config_root.getchildren().index(newest_sdf)+1, new_sdf)
            new_sdf.set("version", str(sdf_version))
            new_sdf.text = sdf_filename
        elif sdf_version == newest_sdf_version:  # Converting the same version, just make sure the path is correct
            if newest_sdf.text != sdf_filename:
                rename(path.join(model_dir, newest_sdf.text),
                       sdf_model_path)
                newest_sdf.text = sdf_filename
        else:  # Converting not to the newest version
            sdf_filename = "model-{}.sdf".format(str(sdf_version).replace('.', '_'))
            sdf_model_path = path.join(model_dir, sdf_filename)
            # Check if older version exists in model.config
            current_sdf = next((x for x in config_sdfs if x.attrib['version'] == str(sdf_version)), None)
            if current_sdf is None:  # Version doesn't exist yet, so add it
                current_sdf = ET.Element("sdf")
                current_sdf.attrib['version'] = str(sdf_version)
                current_sdf.text = sdf_filename
                # Add tag before the first newer version, so at old index of the first newer version
                first_newer_version_sdf = [sdf for sdf in config_sdfs if (float(sdf.attrib['version']) > sdf_version)][-1]
                index_of_newer_vesion = config_root.getchildren().index(first_newer_version_sdf)
                config_root.insert(index_of_newer_vesion, current_sdf)
            elif current_sdf.text != sdf_filename:
                rename(path.join(model_dir, current_sdf.text),
                       sdf_model_path)
                current_sdf.text = sdf_filename

        # Always write model name for the case a model has been moved, so its name needs to changed.
        config_root.find("name").text = model_name
        config_root.find("description").text = model_name

        write_xml_to_file(config_root, model_config_path)

    else:  # SDF model doesn't exist yet
        test_model_path = get_model_path("test_sdf", "sdf")
        if not test_model_path:
            print(bcolors.FAIL + bcolors.BOLD + "Can't find 'test_sdf' model. "
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

    # Write SDF file
    write_xml_to_file(xml, sdf_model_path)

    print(bcolors.OKGREEN + "[{}] Successfully converted to SDF".format(model_name) + bcolors.ENDC)
    return 0


def convert_model_file(model_name: str, model_file: str, recursive: bool = False) -> int:
    """
    Convert a model to SDF based on a model file

    :param model_name: name of the model
    :param model_file: path of the model file
    :param recursive: If true all included models are also converted
    :return: Good: 0, Error: 1
    """
    model_dir = path.dirname(model_file)

    # read yaml file
    with open(model_file, "r") as stream:
        try:
            yml = yaml.load(stream)
        except yaml.YAMLError as e:
            print(bcolors.FAIL + bcolors.BOLD + "[{}] (YAML) ".format(model_name) + str(e) + bcolors.ENDC)
            return 1

    return convert_model_data(yml, model_name, model_dir, recursive)


def convert_model_name(model_name: str, recursive: bool = False) -> int:
    """
    Convert a model to SDF based on the model name.

    :param model_name: Name of the model, model_name/model.yaml should exist in ED_MODEL_PATH
    :param recursive: If true all included models are also converted
    :return: Good: 0, Error: 1
    """
    # strip trailing slash
    if model_name[-1] == "/":
        model_name = model_name[:-1]

    # get model path
    model_file = get_model_path(model_name, "yaml")
    if not model_file:
        print(bcolors.FAIL + bcolors.BOLD + "[{}] No model path found".format(model_name) + bcolors.ENDC)
        return 1

    return convert_model_file(model_name, model_file, recursive)
