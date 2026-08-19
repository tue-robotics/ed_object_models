cmake_minimum_required(VERSION 3.8)
project(ed_object_models)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(
  PROGRAMS
    scripts/convert_yaml_to_sdf
    scripts/create-model
    scripts/dump-ed.py
    scripts/generate_qr_codes.py
    scripts/spawn_sdf_in_gazebo.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY models DESTINATION share/${PROJECT_NAME})

# Sets ED_MODEL_PATH so 'ed' can find the models installed by this package.
set(AMENT_CMAKE_ENVIRONMENT_HOOKS_DESC_ed_object_models_model_path
  "prepend-non-duplicate-if-exists;ED_MODEL_PATH;share/${PROJECT_NAME}/models")
ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/ed_object_models_model_path.sh.in"
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_import test/test_import.py)
endif()

ament_package()
