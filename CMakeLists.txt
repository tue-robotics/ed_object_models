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

###########
## Build ##
###########

MACRO(MODEL_YAML_DIRECTORIES_RECURSIVE return_models return_files curdir)
    FILE(GLOB_RECURSE children ${curdir} model.yaml)
    SET(dir_list "")
    FOREACH(child ${children})
        GET_FILENAME_COMPONENT(dir_path ${child} PATH)
        file(RELATIVE_PATH rel_dir ${curdir} ${dir_path})
        LIST(APPEND dir_list ${rel_dir})
        LIST(APPEND file_list ${child})
    ENDFOREACH(child)
    SET(${return_models} ${dir_list})
    SET(${return_files} ${file_list})
ENDMACRO()

MODEL_YAML_DIRECTORIES_RECURSIVE(MODEL_NAMES MODEL_FILES ${PROJECT_SOURCE_DIR}/models)

find_program(PYTHON python REQUIRED)
find_program(BASH bash REQUIRED)

add_custom_target(SDF_CONVERSION ALL
                  DEPENDS ${MODEL_FILES})
add_custom_command(TARGET SDF_CONVERSION
                   COMMAND ${BASH} -c 'export ED_MODEL_PATH=${PROJECT_SOURCE_DIR}/models && ${PYTHON} ${PROJECT_SOURCE_DIR}/src/${PROJECT_NAME}/conversion_sdf.py ${MODEL_NAMES}'
                   DEPENDS ${MODEL_FILES})

#############
## Testing ##
#############

if (CATKIN_ENABLE_TESTING)
  enable_testing()
  find_program(GIT git REQUIRED)
  add_custom_command(TARGET run_tests_${PROJECT_NAME}
                     COMMAND ${GIT} add ${PROJECT_SOURCE_DIR}/models WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} OUTPUT_VARIABLE add_output RESULT_VARIABLE add_result)
  message(STATUS ${add_output})
  add_custom_command(TARGET run_tests_${PROJECT_NAME}
                     COMMAND ${GIT} diff HEAD ${PROJECT_SOURCE_DIR}/models WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} OUTPUT_VARIABLE diff_output RESULT_VARIABLE diff_result)
  message(STATUS ${diff_output})
  add_custom_command(TARGET run_tests_${PROJECT_NAME}
                     COMMAND ${GIT} reset WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} OUTPUT_VARIABLE reset_output RESULT_VARIABLE reset_result)
  message(STATUS ${reset_output})
  if(NOT ${diff_result} EQUAL 0)
    message(STATUS "diff output:\n${diff_output}")
    message(FATAL_ERROR "Error during: git diff models")
  endif()
  if(NOT ${diff_output} STREQUAL "")
    message(STATUS "diff output:\n${diff_output}")
    message(FATAL_ERROR "Difference in the models folder after SDF conversion, make sure the SDF version of yaml files are committed")
  endif()
endif()
