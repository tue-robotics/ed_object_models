cmake_minimum_required(VERSION 2.8.3)
project(ed_object_models)

## Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS
)

catkin_add_env_hooks(99.ed_object_models SHELLS bash DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/env-hooks)

MACRO(MODEL_YAML_DIRECTORIES_REC return_list curdir)
    FILE(GLOB_RECURSE children ${curdir} model.yaml)
    SET(dir_list "")
    FOREACH(child ${children})
        GET_FILENAME_COMPONENT(dir_path ${child} PATH)
        file(RELATIVE_PATH rel_dir ${curdir} ${dir_path})
        LIST(APPEND dir_list ${rel_dir})
    ENDFOREACH()
    SET(${return_list} ${dir_list})
ENDMACRO()

MODEL_YAML_DIRECTORIES_REC(MODELS ${PROJECT_SOURCE_DIR}/models)

find_program(PYTHON python REQUIRED)
add_custom_target(SDF_CONVERSION ALL)
add_custom_command(TARGET SDF_CONVERSION
                   COMMAND ${PYTHON} ${PROJECT_SOURCE_DIR}/scripts/convert_yaml_to_sdf ${MODELS} WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/scripts)# RESULT_VARIABLE conversion_result)
#if(NOT ${conversion_result} EQUAL 0)
  #message(FATAL_ERROR "Conversion failed")
#endif()


###################################
## catkin specific configuration ##
###################################
catkin_python_setup()

catkin_package()
