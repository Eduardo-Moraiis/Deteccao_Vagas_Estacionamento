cmake_minimum_required(VERSION 3.29)
project(projeto_estacionamento)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1. Faz o CMake ler a sua variável de ambiente do Windows
if(DEFINED ENV{OPENCV_DIR})
    set(OpenCV_DIR $ENV{OPENCV_DIR})
endif()

# 2. Localiza a instalação do OpenCV
find_package(OpenCV REQUIRED)

# Mensagens de confirmação no console do CLion
message(STATUS "--------------------------------------------------")
message(STATUS "OpenCV encontrado com sucesso!")
message(STATUS "Versao: ${OpenCV_VERSION}")
message(STATUS "--------------------------------------------------")

# 3. Cria o executável com o seu main.cpp
add_executable(projeto_estacionamento src/main.cpp)

# 4. Inclui as pastas de cabeçalhos (.hpp) e vincula as bibliotecas (.lib)
target_include_directories(projeto_estacionamento PRIVATE ${OpenCV_INCLUDE_DIRS})
target_link_libraries(projeto_estacionamento PRIVATE ${OpenCV_LIBS})