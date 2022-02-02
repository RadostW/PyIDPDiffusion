#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <stdio.h>
#include <iostream>
#include <sstream>
#include "chain_generator.cpp"

std::string getChainPython(std::string desc)
{
    auto buffer = desc;
    std::vector<double> stericSizes;
    double r;
    std::replace( buffer.begin(), buffer.end(), '[', ' ');
    std::replace( buffer.begin(), buffer.end(), ']', ' ');
    std::replace( buffer.begin(), buffer.end(), ',', ' ');
    int consumed=0,chars=0;
    while(sscanf(buffer.c_str()+consumed,"%lf %n",&r,&chars) == 1)
    {
        consumed +=chars; //Update number of chars consumed by sscanf.
        stericSizes.push_back(r);
    }
    
    
    auto chain = getChain(stericSizes.size(),0,stericSizes);

    std::stringstream ss;
    for(int i=0;i<chain.size();i++)    
    {
        ss << chain[i].x << " " << chain[i].y << " " << chain[i].z << "\n";
    }

    return ss.str();
}



PYBIND11_MODULE(generator_interface, m) {
    m.doc() = "pybind11 api for c++ chain generation module"; // optional module docstring

    m.def("getChainPython", &getChainPython, "Generates chain out of description");
}
