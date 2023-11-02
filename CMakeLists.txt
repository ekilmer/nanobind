cmake_minimum_required(VERSION 3.15...3.27)

project(nanobind LANGUAGES NONE)

string(
  COMPARE EQUAL
  "${CMAKE_SOURCE_DIR}" "${PROJECT_SOURCE_DIR}"
  PROJECT_IS_TOP_LEVEL
)

if(PROJECT_IS_TOP_LEVEL)
  option(NB_DEVELOPER_MODE "Enable developer mode" OFF)

  option(NB_PYTHON_INSTALLATION "Install nanobind for use from Python" OFF)
  mark_as_advanced(NB_PYTHON_INSTALLATION)
endif()

option(NB_SKIP_INSTALL_RULES "Skip installing nanobind files" ${CMAKE_SKIP_INSTALL_RULES})
option(NB_USE_SUBMODULE_DEPS "Use dependency(s) from Git submodule(s)" ON)

# ---------------------------------------------------------------------------
# Check whether submodule(s) are initialized for installation, if chosen
# ---------------------------------------------------------------------------

if(NB_USE_SUBMODULE_DEPS)
  # This variable is used to add the submodule(s) in `cmake/nanobind.cmake`
  set(NB_EXT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/ext")
  if (NOT IS_DIRECTORY "${NB_EXT_DIR}/robin_map/include")
    message(FATAL_ERROR "The nanobind dependencies are missing! "
      "You probably did not clone the project with --recursive. It is possible to recover "
      "by invoking\n$ git submodule update --init --recursive")
  endif()
endif()

# ---------------------------------------------------------------------------
# Installation rules
# ---------------------------------------------------------------------------

if(NOT NB_SKIP_INSTALL_RULES)
  include(CMakePackageConfigHelpers)
  set(CMAKE_INSTALL_INCLUDEDIR "include"
    CACHE PATH "Installation path for header files"
  )
  set(NB_INSTALL_SRCDIR "src/nanobind"
    CACHE PATH "Installation path for source files"
  )
  set(CMAKE_INSTALL_DATAROOTDIR "share"
    CACHE PATH "Installation path for read-only architecture-independent data root"
  )
  set(NB_INSTALL_CMAKEDIR "${CMAKE_INSTALL_DATAROOTDIR}/nanobind/cmake"
    CACHE PATH "Installation path for CMake files"
  )

  install(
    DIRECTORY include/
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
  )

  install(
    DIRECTORY src/
    DESTINATION "${NB_INSTALL_SRCDIR}"
    PATTERN "*.py" EXCLUDE
  )

  if(DEFINED NB_PYTHON_INSTALLATION AND NB_PYTHON_INSTALLATION)
    install(
      FILES src/__init__.py src/__main__.py
      DESTINATION .
    )
  endif()

  if(NB_USE_SUBMODULE_DEPS)
    install(
      DIRECTORY "${NB_EXT_DIR}/robin_map/include/"
      DESTINATION "${NB_INSTALL_SRCDIR}/ext/robin_map/include"
    )
    install(
      FILES
        "${NB_EXT_DIR}/robin_map/tsl-robin-map.natvis"
        "${NB_EXT_DIR}/robin_map/CMakeLists.txt"
      DESTINATION "${NB_INSTALL_SRCDIR}/ext/robin_map"
    )
  endif()

  configure_package_config_file(
    nanobind-config.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/nanobind-config.cmake"
    INSTALL_DESTINATION "${NB_INSTALL_CMAKEDIR}"
    PATH_VARS
      NB_INSTALL_CMAKEDIR
      NB_INSTALL_SRCDIR
      CMAKE_INSTALL_INCLUDEDIR
  )
  install(
    FILES "${CMAKE_CURRENT_BINARY_DIR}/nanobind-config.cmake"
    DESTINATION ${NB_INSTALL_CMAKEDIR}
  )

  install(
    DIRECTORY cmake/
    DESTINATION "${NB_INSTALL_CMAKEDIR}"
  )
endif()

# ---------------------------------------------------------------------------
# Return early if the user is not developing nanobind using `add_subdirectory`
# or is not developing the codebase.
# Since we don't really build anything when it's a top-level project (aside from
# tests), returning early prevents needless dependency checks when we'll just be
# installing files. This also makes it easier to package nanobind.
# ---------------------------------------------------------------------------

if(NOT NB_DEVELOPER_MODE AND PROJECT_IS_TOP_LEVEL)
  return()
elseif(NB_DEVELOPER_MODE AND NOT PROJECT_IS_TOP_LEVEL)
  message(
    AUTHOR_WARNING
    "Developer mode is intended for developers of nanobind"
  )
endif()

# ---------------------------------------------------------------------------
# Do a release build if nothing was specified
# ---------------------------------------------------------------------------

if(PROJECT_IS_TOP_LEVEL AND NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  message(STATUS "nanobind: setting build type to 'Release' as none was specified.")
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release"
    "MinSizeRel" "RelWithDebInfo")
endif()

# ---------------------------------------------------------------------------
# Compile with a few more compiler warnings turned on
# ---------------------------------------------------------------------------

if(MSVC)
  if(CMAKE_CXX_FLAGS MATCHES "/W[0-4]")
    string(REGEX REPLACE "/W[0-4]" "/W4" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
  else()
    add_compile_options(/W4)
  endif()
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  add_compile_options(-Wall -Wextra -Wno-unused-local-typedefs)
endif()

# ---------------------------------------------------------------------------
# Include nanobind cmake functionality
# ---------------------------------------------------------------------------

# These are cache variables so that the nanobind functions work when using
# `add_subdirectory(nanobind)`
set(NB_SRC_DIR     ${PROJECT_SOURCE_DIR}/src
  CACHE INTERNAL "Directory containing nanobind source files")
set(NB_INCLUDE_DIR ${PROJECT_SOURCE_DIR}/include
  CACHE INTERNAL "Directory containing nanobind include files")
set(NB_CMAKE_DIR   ${PROJECT_SOURCE_DIR}/cmake
  CACHE INTERNAL "Directory containing nanobind cmake files")

include(cmake/nanobind.cmake)

# ---------------------------------------------------------------------------
# Guard against configuring tests if not wanting to develop nanobind
# ---------------------------------------------------------------------------

if(NOT NB_DEVELOPER_MODE)
  return()
elseif(NOT PROJECT_IS_TOP_LEVEL)
  message(AUTHOR_WARNING "Developer mode is intended for developers of nanobind")
endif()

include(CTest)
if(BUILD_TESTING)
  add_subdirectory(tests)
endif()
