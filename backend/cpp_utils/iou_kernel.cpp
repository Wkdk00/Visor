#include <pybind11/pybind11.h>
#include <algorithm>
#include <tuple>

namespace py = pybind11;

// логика функции IoU
double calculate_iou_cpp(std::tuple<float, float, float, float> box1, 
                         std::tuple<float, float, float, float> box2) {
    
    auto [x1_min, y1_min, x1_max, y1_max] = box1;
    auto [x2_min, y2_min, x2_max, y2_max] = box2;

    float inter_x1 = std::max(x1_min, x2_min);
    float inter_y1 = std::max(y1_min, y2_min);
    float inter_x2 = std::min(x1_max, x2_max);
    float inter_y2 = std::min(y1_max, y2_max);

    float inter_w = std::max(0.0f, inter_x2 - inter_x1);
    float inter_h = std::max(0.0f, inter_y2 - inter_y1);
    float inter_area = inter_w * inter_h;

    float area1 = (x1_max - x1_min) * (y1_max - y1_min);
    float area2 = (x2_max - x2_min) * (y2_max - y2_min);
    float union_area = area1 + area2 - inter_area;

    if (union_area == 0) return 0.0;
    return (double)(inter_area / union_area);
}

// Склеивание с Python
PYBIND11_MODULE(cpp_iou, m) {
    m.doc() = "Fast C++ IoU implementation"; 
    m.def("calculate_iou", &calculate_iou_cpp, "Calculate IoU between two boxes");
}