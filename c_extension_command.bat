g++ -std=c++14 -shared -fPIC -static-libgcc -static-libstdc++ -I./include/ -I./pybind11/include/ -I/usr/include/python3.9 -I/usr/lib/python3.9/site-packages/pybind11/include generator_interface.cpp -o generator_interface.cpython-39-x86_64-windows.dll  -L/usr/lib -lpython3.9 -lintl -ldl     -mwindows -L libwinpthread-1.dll