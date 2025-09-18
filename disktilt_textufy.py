# ANDRIX x CRAL ® 2025 🤙
# 
# Generate text files with tracers data to use in Unity for the creation of 2D textures read by a VFX graph
# 
# This file uses sarracen to read a SHAMROCK data dump

import sarracen

source_file = "./data/disktilt_dump_0314.sham"
sdf = sarracen.read_shamrock(source_file)

print(sdf.describe())
