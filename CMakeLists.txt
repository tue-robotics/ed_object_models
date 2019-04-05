cmake_minimum_required(VERSION 2.8.3)
project(ed_object_models)

## Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS
)

catkin_add_env_hooks(99.ed_object_models SHELLS bash DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/env-hooks)

###################################
## catkin specific configuration ##
###################################
catkin_python_setup()

catkin_package()

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
                   COMMAND ${PYTHON} ${PROJECT_SOURCE_DIR}/src/${PROJECT_NAME}/conversion_sdf.py ${MODELS} WORKING_DIRECTORY ${PROJECT_SOURCE_DIR})


if (CATKIN_ENABLE_TESTING)
  find_program(GIT git REQUIRED)
  execute_process(COMMAND ${GIT} diff ${PROJECT_SOURCE_DIR}/models WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/scripts OUTPUT_VARIABLE output RESULT_VARIABLE result)
  if(NOT ${result} EQUAL 0)
    message(FATAL_ERROR "Error during: git diff")
  endif()
  if(NOT ${output} STREQUAL "")
    message(SEND_ERROR ${output})
    message(FATAL_ERROR "Difference in the models folder after SDF conversion, make sure the SDF version of yaml files are committed")
  endif()
endif()
