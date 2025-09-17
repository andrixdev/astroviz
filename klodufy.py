# ANDRIX ® 2025: generate 3D textures for Unity out of pointcloud files
# Klodu comes from Klodo, the japanese name of Final Fantasy VII character Cloud
# Source data from CRAL, bifluid by Benoit Commercon, brown dwarf by Adnan Ali Ahmad

import numpy as np
import math
import random

def remap (input, source_min, source_max, target_min, target_max):
    return target_min + (target_max - target_min) * (input - source_min) / (source_max - source_min)

def write_unity_header (destination_file, file_name, base_size, data_size):
    destination_file.write("%YAML 1.1\n")
    destination_file.write("%TAG !u! tag:unity3d.com,2011:\n")
    destination_file.write("--- !u!117 &11700000\n")
    destination_file.write("Texture3D:\n")
    destination_file.write("  m_ObjectHideFlags: 0\n")
    destination_file.write("  m_CorrespondingSourceObject: {fileID: 0}\n")
    destination_file.write("  m_PrefabInstance: {fileID: 0}\n")
    destination_file.write("  m_PrefabAsset: {fileID: 0}\n")
    destination_file.write("  m_Name: " + file_name + "\n")
    destination_file.write("  m_ImageContentsHash:\n")
    destination_file.write("    serializedVersion: 2\n")
    destination_file.write("    Hash: 00000000000000000000000000000000\n")
    destination_file.write("  m_IsAlphaChannelOptional: 0\n")
    destination_file.write("  serializedVersion: 4\n")
    destination_file.write("  m_ColorSpace: 0\n")
    destination_file.write("  m_Format: 21\n")
    destination_file.write("  m_Width: " + str(base_size) + "\n")
    destination_file.write("  m_Height: " + str(base_size) + "\n")
    destination_file.write("  m_Depth: " + str(base_size) + "\n")
    destination_file.write("  m_MipCount: 1\n")
    destination_file.write("  m_DataSize: " + str(data_size) + "\n")
    destination_file.write("  m_TextureSettings:\n")
    destination_file.write("    serializedVersion: 2\n")
    destination_file.write("    m_FilterMode: 1\n")
    destination_file.write("    m_Aniso: 1\n")
    destination_file.write("    m_MipBias: 0\n")
    destination_file.write("    m_WrapU: 1\n")
    destination_file.write("    m_WrapV: 1\n")
    destination_file.write("    m_WrapW: 1\n")
    destination_file.write("  m_UsageMode: 0\n")
    destination_file.write("  m_IsReadable: 1\n")
    destination_file.write("  image data: " + str(data_size) + "\n")
    destination_file.write("  _typelessdata: ")

def write_unity_footer (destination_file):
    destination_file.write("\n")
    destination_file.write("  m_StreamData:\n")
    destination_file.write("    serializedVersion: 2\n")
    destination_file.write("    offset: 0\n")
    destination_file.write("    size: 0\n")
    destination_file.write("    path: \n")

def parse_int_to_formatted_hex (value):
    hex_value = hex(int(value))[2:] # Remove '0x' of hexadecimal notation
    
    hexlen = len(str(hex_value)) # Make sure we always have 4 characters
    if (hexlen == 1):
        hex_value = "000" + str(hex_value)
    elif (hexlen == 2):
        hex_value = "00" + str(hex_value)
    elif (hexlen == 3):
        hex_value = "0" + str(hex_value)
            
    return hex_value

# Count points in pointcloud to create 3D texture (voxel cloud)
# Final texture coordinates are implict, between [0, 1] [0, 1] [0, 1], sliced into size³ cubes
# Source coordinates have to be remapped to [0, 1] [0, 1] [0, 1]
def klodufy (path, size, source_min, source_max, max_resolution):
    arr = np.loadtxt(path)
    leng = arr.shape[0]
    total_size = size * size * size
    #print("Source data shape is " + str(arr.shape))
    print("Source row count: " + str(leng))
    print("Output cube size: " + str(size) + "³ = " + str(total_size))
    
    # Init empty 3D texture
    klodu = []
    voxel_size = (1 - 0) * 1 / size
    for c in range(0, total_size):
        klodu.append(0)
        
    # Prepare export file
    file_name = "aa-klodu-3D-tex-" + str(size) + "-logsum-001"
    destination_file = open("output/" + file_name + ".asset", "w")
    
    # Generate Unity header
    base_size = size
    data_size = 2 * base_size * base_size * base_size
    write_unity_header(destination_file, file_name, base_size, data_size)
    
    # Loop into source data, find nearest voxel and increment its intensity
    # Also detect max value
    max_value = 0
    for i in range(0, leng):
        line = arr[i]
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
        klodu[k] += 10**(vv + 15)
        
        if (klodu[k] > max_value):
            max_value = klodu[k]
        
    print("Max value is " + str(max_value))
    
    # Normalize so it fits max resolution, parsing to hex and writing to file
    print("Normalizing (over " + str(len(klodu)) + " values), parsing to hex and writing to file...")
    for j in range (0, len(klodu)):
        klodu[j] = round(klodu[j] / max_value * max_resolution)
        
        # Write final klodu values to text file
        hex_value = parse_int_to_formatted_hex(klodu[j])
        
        destination_file.write(str(hex_value))
        
        # Print out some values while waiting...
        if (j % int(len(klodu)/60) == 0):
            #print(str(klodu[j]) + " " + str(max_value) + " " + str(max_resolution))
            print(str(j) + "th value is: " + str(hex_value) + " (" + str(100 * klodu[j] / max_resolution) + "% of max intensity)")
    
    # Now... time to smooth values by looking at neighbours...
    # Coming soon...
    
    
    # Generate Unity footer
    write_unity_footer(destination_file)
    
    print("Done!")

# Klodufy (voxelize) already cleaned Commerc bifluid file
source_file_name = "./data/bin1_bifluid_00045_clean3.txt"
size = 10
source_min = 0
source_max = 4
max_resolution = 65536 - 1 # 2^16 (intensities exported to 16-bit single-channel 3D-texture, TextureFormat.R16 in Unity)
# klodufy(source_file_name, size, source_min, source_max, max_resolution)

# Parse .npy cube to Unity 3D texture
def klodufy_npy (source_file, size, destination_file_name, max_resolution, rounding_mode, logarithmic_mode, testing_mode):
    data = np.load(source_file)
    print("Data shape is " + str(data.shape) + " with a total of " + str(data.size) + " elements.")
    
    # Prepare export file
    destination_file = open("output/" + destination_file_name + ".asset", "w")
    
    # Generate Unity header
    base_size = data.shape[0]
    data_size = 2 * base_size * base_size * base_size
    write_unity_header(destination_file, destination_file_name, base_size, data_size)
    
    # Testing mode (don't compute all values)
    testing_step = 10
    step = testing_step if testing_mode else 1
    
    # Detect extreme values
    min_value = float("inf")
    max_value = float("-inf")
    i = 0
    for a in range(0, data.shape[0]):
        for b in range(0, data.shape[1]):
            for c in range(0, data.shape[2]):
                i += 1
                
                # Keep only 2 decimals
                if (i % step == 0):
                    abc = math.log10(data[a][b][c]) if logarithmic_mode else data[a][b][c]
                    abc = round(abc, 2) if rounding_mode else abc
                    data[a][b][c] = abc
                    # print(abc)
                    
                    if (abc > max_value):
                        max_value = abc
                    if (abc < min_value):
                        min_value = abc
                    
                    # if (i % testing_step == 0):
                        # print(str(i) + "th value is: " + str(abc))
    
    print("Min value is: " + str(min_value))
    print("Max value is: " + str(max_value))
    
    if (max_value == 0):
        print("Problem captain, MAX VALUE IS ZERO! ABORT! ABORT!")
        return False
    
    # Normalize so it fits max resolution
    print("Normalizing (over " + str(data.size) + " values), parsing to hex and writing to file...")
    j = 0
    for a in range(0, data.shape[0]):
        for b in range(0, data.shape[1]):
            for c in range(0, data.shape[2]):
                j += 1
                
                if (j % step == 0):
                    new_value = round(remap(data[a][b][c], min_value, max_value, 0, max_resolution))
                    data[a][b][c] = new_value
                    hex_value = parse_int_to_formatted_hex(new_value)
                    destination_file.write(str(hex_value))
                    
                    # Print out some values while waiting...
                    # if (j % testing_step == 0):
                        # print(str(j) + "th hexadecimal value is: " + str(hex_value))
    
    # Generate Unity footer
    write_unity_footer(destination_file)

# Brownie
source_file = "./data/brownie_B_field_stack_01863.npy"
size = 237
destination_file_name = "klodu-brown-dwarf-237"
rounding_mode = True
logarithmic_mode = False
testing_mode = False
# klodufy_npy(source_file, size, destination_file_name, max_resolution, rounding_mode, logarithmic_mode, testing_mode) # Always outputs a 237³ file

# Dustyturb npy cloud
source_file = "./data/dustyturb_density_reshaped_00524.npy"
size = 256
destination_file_name = "klodu-dustyturb-256"
rounding_mode = False
logarithmic_mode = True
testing_mode = True
klodufy_npy(source_file, size, destination_file_name, max_resolution, rounding_mode, logarithmic_mode, testing_mode)

# Dustyturb .dat (later)

# Dustyturb npy tracers
source_file = "./data/dustyturb_tracers_00524.npy"
data = np.load(source_file)
print("Data shape is " + str(data.shape) + " with a total of " + str(data.size) + " elements.")
print(len(data[:][0]))
print(data.shape[0])
for i in range(0, 1000):
    # print("1054 is " + str(data[i][1054]) + " while 9054 is " + str(data[i][9054]) )
    x = data[0][i]
    y = data[1][i]
    z = data[2][i]
    
    print(str(x) + " " + str(y) + " " + str(z))
    
    