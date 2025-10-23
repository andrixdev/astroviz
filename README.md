# Astroviz

Python scripts to generate 2D and 3D textures for Unity out of various astrophysics data formats  

**klodufy.py** creates 3D textures for Unity out of cube density maps (voxel clouds)  
**sph_textufy.py** creates text files with rows of data for Unity to transform into 2D textures  

## Usage

- Install Python 3.13 (max verison supported by *sarracen* package as of 2025-10)  
- Install *numpy*, *scipy* and *sarracen* packages running `pip install numpy`, `pip install scipy` and `pip install sarracen`  
- Run `py klodufy.py` or `python klodufy.py` depending on your main Python CLI call.  
- The *data* directory contains sources, while *output* contains your exported text files.  
- The *data* directory is left empty, for you to fill it with relevant data files.  
- Adapt the script by commenting or uncommenting revelant code sections.  
- Edit file according to your needs.   
