find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_ELRS_MODULE gnuradio-elrs_module)

FIND_PATH(
    GR_ELRS_MODULE_INCLUDE_DIRS
    NAMES gnuradio/elrs_module/api.h
    HINTS $ENV{ELRS_MODULE_DIR}/include
        ${PC_ELRS_MODULE_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_ELRS_MODULE_LIBRARIES
    NAMES gnuradio-elrs_module
    HINTS $ENV{ELRS_MODULE_DIR}/lib
        ${PC_ELRS_MODULE_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-elrs_moduleTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_ELRS_MODULE DEFAULT_MSG GR_ELRS_MODULE_LIBRARIES GR_ELRS_MODULE_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_ELRS_MODULE_LIBRARIES GR_ELRS_MODULE_INCLUDE_DIRS)
