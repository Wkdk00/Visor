cmake_minimum_required(VERSION 3.10)
project(cpp_iou)

find_package(pybind11 REQUIRED)

pybind11_add_module(cpp_iou iou_kernel.cpp)