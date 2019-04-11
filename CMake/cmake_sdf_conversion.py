#!/usr/bin/env python
# This file isn't executable. So can't be run by ROS. This is only here to be used by the CMake.

import argparse
import hashlib
import os
import re
import sys


def model_files(model_path):
    # type: (str) -> ([str])
    mfiles = []
    for root, dirs, files in os.walk(model_path):
        for filename in files:
            if file.endswith("model.yaml"):
                mfiles.append(os.path.relpath(os.path.join(root, filename), model_path))
    return mfiles


def modified_model_files(model_path, hash_path):
    # type: (str, str) -> ([str])
    all_models = model_files(model_path)
    mod_models = []
    for model in all_models:
        hash_file = hash_filename(model)
        hash_file_path = os.path.join(hash_path, hash_file)

        if not os.path.isfile(hash_file_path):
            mod_models.append(model)
            continue

        with open(hash_file_path, "r") as f:
            old_hash = f.read()
        current_hash = file_hash(os.path.join(model_path, model))
        if old_hash != current_hash:
            mod_models.append(model)

    return mod_models


def hash_filename(model_file):
    # type: (str) -> str
    return re.sub("[/.]", "_", model_file)


def file_hash(file_path):
    # type: (str) -> str
    with open(file_path, "r") as f:
        file_content = f.read()
    h = hashlib.sha1()
    h.update(file_content)
    return h.hexdigest()


def write_model_hash(model_file, model_path, hash_path):
    model_hash = file_hash(os.path.join(model_path, model_file))
    hash_file_path = os.path.join(hash_path, hash_filename(model_file))
    if not os.path.exists(os.path.dirname(hash_file_path)):
        os.makedirs(os.path.dirname(hash_file_path))
    with open(hash_file_path, "w") as f:
        f.write(model_hash)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert custom ED YAML model to SDF")
    parser.add_argument("package_path", type=str, nargs=1)
    parser.add_argument("build_path", type=str, nargs=1)
    arguments = parser.parse_args()
    package_path = os.path.normpath(arguments.package_path[0])
    build_path = os.path.normpath(arguments.build_path[0])

    model_path = os.path.join(package_path, "models")
    hash_path = os.path.join(build_path, "model_hashes")

    mod_model_files = modified_model_files(model_path, hash_path)

    sys.path.append(os.path.join(os.path.abspath(package_path), "src/ed_object_models"))
    from conversion_sdf import main

    for model_file in mod_model_files:
        model_name = os.path.dirname(model_file)
        errc = main(model_name)
        if errc != 0:
            sys.exit(errc)
        write_model_hash(model_file, model_path, hash_path)

    sys.exit(0)
