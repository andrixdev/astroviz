# ANDRIX ® 2025: generate 3D textures for Unity out of pointcloud files
# Klodu comes from Klodo, the japanese name of Final Fantasy VII character Cloud
import numpy as np
import math
import random


def remap (input, source_min, source_max, target_min, target_max):
    return target_min + (target_max - target_min) * (input - source_min) / (source_max - source_min)
    
# Count points in pointcloud to create 3D texture (voxel cloud)
# Final texture coordinates are implict, between [0, 1] [0, 1] [0, 1], sliced into size³ cubes
# Source coordinates have to be remapped to [0, 1] [0, 1] [0, 1]
def klodufy (path, size, source_min, source_max, max_resolution):
    arr = np.loadtxt(path)
    print("Data shape is " + str(arr.shape))
    
    # Init empty 3D texture
    klodu = []
    voxel_size = (1 - 0) * 1 / size
    for c in range(0, size * size * size):
        klodu.append(0)
        
    # Prepare export file
    file_to_write = open('output/aa-klodu-' + str(size) + '.txt', "w")
    
    # Loop into source data
    leng = arr.shape[0]
    max_value = 0
    for i in range(0, leng):
        line = arr[i]
        if (i % 1 == 0):
            
            x = line[0]
            y = line[1]
            z = line[2]
            v = line[3]
            xx = remap(x, source_min, source_max, 0, 1)
            yy = remap(y, source_min, source_max, 0, 1)
            zz = remap(z, source_min, source_max, 0, 1)
            vv = v
            
            # Get voxel index from remapped source position
            ix = xx / voxel_size
            fix = int(ix) # floor
            fiy = int(yy  / voxel_size)
            fiz = int(zz / voxel_size)
            #print("x is " + str(x) + ", xx is " + str(xx) + ", ix is " + str(ix) + ", fix is " + str(fix))
            
            #print("klodu target indexes are (" + str(fix) + ", " + str(fiy) + ", " + str(fiz) + ")")
            
            # Fill target klodu with some value
            kx = fix
            ky = fiy * size
            kz = fiz * size * size
            k = kx + ky + kz
            klodu[k] += 1
            
            if (klodu[k] > max_value):
                max_value = klodu[k]
            
            #print(klodu[k])
            
    print("Max value is " + str(max_value))
    print("Normalizing...")
    # Normalize so it fits max resolution
    for j in range (0, len(klodu)):
        klodu[j] = round(klodu[j] / max_value * max_resolution)
        
        # Write final klodu values to text file
        hex_value = hex(int(klodu[j]))[2:]
        file_to_write.write(str(hex_value))
        
        #if (j % 1 == 0):
            #print(str(klodu[j]) + " " + str(max_value) + " " + str(max_resolution))
            #print(hex_value)
        
    print("Done!")
    
# Klodufy (voxelize) already cleaned Commerc bifluid file
file_name = './data/bin1_bifluid_00045_clean3.txt'
size = 8
source_min = 0
source_max = 4
max_resolution = 65536 - 1 # 2^16 (intensities exported to 16-bit single-channel 3D-texture)
klodufy(file_name, size, source_min, source_max, max_resolution)
