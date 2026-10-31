cmake_minimum_required(VERSION 3.29)
project(projeto_estacionamento)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
FetchContent_Declare(
        pugixml
        GIT_REPOSITORY https://github.com/zeux/pugixml.git
        GIT_TAG v1.14
)
FetchContent_MakeAvailable(pugixml)

if(DEFINED ENV{OPENCV_DIR})
    set(OpenCV_DIR $ENV{OPENCV_DIR})
endif()
find_package(OpenCV REQUIRED)

include_directories(include ${OpenCV_INCLUDE_DIRS})

set(SOURCES
        src/main.cpp
        src/DatasetParser.cpp
        src/ParkingPipeline.cpp
        src/Evaluator.cpp
)

set(HEADERS
        include/DatasetParser.hpp
        include/ParkingPipeline.hpp
        include/Evaluator.hpp
)

add_executable(projeto_estacionamento ${SOURCES} ${HEADERS})
target_link_libraries(projeto_estacionamento PRIVATE ${OpenCV_LIBS} pugixml::pugixml)