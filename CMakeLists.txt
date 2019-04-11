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

find_program(PYTHON python REQUIRED)
find_program(BASH bash REQUIRED)

add_custom_target(SDF_CONVERSION ALL
                  DEPENDS ${MODEL_FILES})
add_custom_command(TARGET SDF_CONVERSION
                   COMMAND ${BASH} -c 'export ED_MODEL_PATH=${PROJECT_SOURCE_DIR}/models && ${PYTHON} ${PROJECT_SOURCE_DIR}/CMake/cmake_sdf_conversion.py ${PROJECT_SOURCE_DIR} ${PROJECT_BINARY_DIR}'
                   DEPENDS ${MODEL_FILES})


#############
## Testing ##
#############

if (CATKIN_ENABLE_TESTING)
  find_program(GIT git REQUIRED)
  execute_process(COMMAND ${GIT} add ${PROJECT_SOURCE_DIR}/models WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} OUTPUT_VARIABLE add_output RESULT_VARIABLE add_result)
  execute_process(COMMAND ${GIT} diff HEAD ${PROJECT_SOURCE_DIR}/models WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} OUTPUT_VARIABLE diff_output RESULT_VARIABLE diff_result)
  execute_process(COMMAND ${GIT} reset WORKING_DIRECTORY ${PROJECT_SOURCE_DIR} OUTPUT_VARIABLE reset_output RESULT_VARIABLE reset_result)
  if(NOT ${diff_result} EQUAL 0)
    message(STATUS "diff output:\n${diff_output}")
    message(FATAL_ERROR "Error during: git diff models")
  endif()
  if(NOT ${diff_output} STREQUAL "")
    message(STATUS "diff output:\n${diff_output}")
    message(FATAL_ERROR "Difference in the models folder after SDF conversion, make sure the same version of the SDF and YAML model are committed")
  endif()
endif()
