# ANDRIX ® 2025: generate 3D textures for Unity out of pointcloud files
# Klodu comes from Klodo, the japanese name of Final Fantasy VII character Cloud
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
    
    # Loop into source data
    
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
            klodu[k] += 10**(vv + 15)
            
            if (klodu[k] > max_value):
                max_value = klodu[k]
            
            #print(klodu[k])
            
    print("Max value is " + str(max_value))
    
    # Normalize so it fits max resolution
    print("Normalizing... over " + str(len(klodu)) + " values...")
    for j in range (0, len(klodu)):
        klodu[j] = round(klodu[j] / max_value * max_resolution)
        
        # Write final klodu values to text file
        hex_value = hex(int(klodu[j]))[2:] # Remove '0x' of hexadecimal notation
        
        hexlen = len(str(hex_value)) # Make sure we always have 4 characters
        if (hexlen == 1):
            hex_value = "000" + str(hex_value)
        elif (hexlen == 2):
            hex_value = "00" + str(hex_value)
        elif (hexlen == 3):
            hex_value = "0" + str(hex_value)
            
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
size = 100
source_min = 0
source_max = 4
max_resolution = 65536 - 1 # 2^16 (intensities exported to 16-bit single-channel 3D-texture, TextureFormat.R16 in Unity)
klodufy(source_file_name, size, source_min, source_max, max_resolution)
