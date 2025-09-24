# ANDRIX ® 2025 🤙
# 
# Generate 3D textures for Unity out of voxel cubes or pointcloud files
#
# Klodu comes from Klodo, the japanese name of Final Fantasy VII character Cloud
# Source data from CRAL - Centre de Recherche Astrophysique de Lyon

import math
import random
import os # for Fortran .dat
import numpy as np # for .npy & Fortran .dat
from scipy.io import FortranFile # for Fortran .dat
import datetime

def remap (input, source_min, source_max, target_min, target_max, clamp_mode):
    if (clamp_mode & (input < source_min)):
        return target_min
    elif (clamp_mode & (input > source_max)):
        return target_max
    else:
        return target_min + (target_max - target_min) * (input - source_min) / (source_max - source_min)

def write_unity_header (destination_file, file_name, base_size, testing_density, dimensionality):
    actual_size = math.floor(base_size * testing_density)
    data_size = 2 * dimensionality * (actual_size ** 3)
    data_format = "21" if dimensionality == 1 else "23"
    
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
    destination_file.write("  m_Format: " + data_format + "\n")
    destination_file.write("  m_Width: " + str(actual_size) + "\n")
    destination_file.write("  m_Height: " + str(actual_size) + "\n")
    destination_file.write("  m_Depth: " + str(actual_size) + "\n")
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
    elif (hexlen == 4):
        hex_value = hex_value
    else:
        print("Sir we have a serious problem here, one hew value is either to short or too long!")
            
    return hex_value

def round_to_n(x, n):
    return round(x, -int(math.floor(round(math.log10(abs(x)) - n + 1))))


# Count points in pointcloud to create 3D texture (voxel cloud)
# Final texture coordinates are implict, between [0, 1] [0, 1] [0, 1], sliced into size³ cubes
# Source coordinates have to be remapped to [0, 1] [0, 1] [0, 1]
def klodufy_txt (path, size, source_min, source_max, max_resolution):
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
    
    # Set max resolution for hex values
    max_resolution = 65536 - 1 # 2^16, starts at 0
    
    # Loop into source data, find nearest voxel and increment its intensity
    # Also detect max value
    max_value = 0
    for i in range(0, leng):
        line = arr[i]
        x = line[0]
        y = line[1]
        z = line[2]
        v = line[3]
        xx = remap(x, source_min, source_max, 0, 1, False)
        yy = remap(y, source_min, source_max, 0, 1, False)
        zz = remap(z, source_min, source_max, 0, 1, False)
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
source_file_name = "./data/bifluid_bin1_00045_clean3.txt"
size = 10
source_min = 0
source_max = 4
# klodufy_txt(source_file_name, size, source_min, source_max)

# file_type_token: "NUMPY" or "DAT"
def prepare_data_cube (source_file, file_type_token):
    
    if (file_type_token == "NUMPY"):
        data = np.load(source_file)
        
        print("Data shape is " + str(data.shape) + " with a total of " + str(data.size) + " elements.")
        
        return data
        
    elif (file_type_token == "DAT"):
        f = FortranFile(os.path.expanduser(source_file), 'r')
        
        sx, sy, sz = f.read_ints(np.int32) # just the size values
        data = f.read_reals(np.float32).reshape((sx, sy, sz), order='F')
        f.close()
        
        return data
        
    else:
        print("[prepare_data_cube(...)] Unknown file type token: " + file_type_token)
        
        return False
    
# Create Unity 3D texture out of data cube
# input dataset should include xyz
# 'dimensionality' of 1 generates a 3D texture with "R" signel channel
# 'dimensionality' of 3 generates a 3D texture with "RGB" channels
# 1-dimension intensities are exported to 16-bit single-channel 3D-texture, TextureFormat.R16 in Unity
# 3-dimension intensities are exported to 3 x 16-bit RGB 3D-textures, TextureFormat.RGB48 in Unity
def klodufy (source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez):
    
    # Testing mode inits
    testing_density = min(1, testing_density) # Make sure it don't go krazy (> 1)
    testing_value = round(1/testing_density)
    
    # Hello
    destination_file_name = destination_file_name + ("" if testing_value == 1 else ("-1-in-" + str(testing_value)))
    destination_file_name = destination_file_name + ("-log" if logarithmic_mode else "") 
    print("Starting work on " + destination_file_name + "...")
    print("type: " + file_type_token + ", size: " + str(size) + ", dimensionality: " + str(dimensionality) + ", rounding mode " + ("on" if rounding_mode else "off") + ", logarithmic mode " + ("on" if logarithmic_mode else "off") + ", testing density: 1 in " + str(testing_value) + "³ == 1 in " + str(testing_value ** 3) + ", number of logs: " + str(nb_logs))
    
    # Load data cube
    data = prepare_data_cube(source_file, file_type_token)
    
    # Prepare export file
    destination_file = open("output/" + destination_file_name + ".asset", "w")
    
    # Generate Unity header
    base_size = data.shape[0]
    base_count = base_size * base_size * base_size
    actual_count = math.floor(base_count * (testing_density ** 3))
    write_unity_header(destination_file, destination_file_name, base_size, testing_density, dimensionality)
    
    # Set max resolution for hex values
    max_resolution = 65536 - 1 # 2^16, starts at 0
    
    # Track time taken
    start_time = datetime.datetime.now()
    
    # LOOP 1: detect extreme values, maybe round or logify
    log_ratio = "all of " if testing_value == 1 else ("1 in " + str(testing_value ** 3) + " of all ")
    print("Parsing " + log_ratio +  str(base_count) + " (== " + str(actual_count) + ") rows while scanning for min & max...")
    min_value = float("inf")
    max_value = float("-inf")
    i = 0
    nb_logs = nb_logs + 1
    x_range = math.floor(data.shape[0] * testing_density)
    y_range = math.floor(data.shape[1] * testing_density)
    z_range = math.floor(data.shape[2] * testing_density)
    step = math.floor(data.shape[0] / x_range)
    
    for a in range(0, x_range):
        for b in range(0, x_range):
            for c in range(0, z_range):
                i += step
                aa = a * step
                bb = b * step
                cc = c * step
                if (dimensionality == 1): # 1 dim
                    v = data[aa][bb][cc]
                    
                    if (logarithmic_mode):
                        v = math.log10(v)
                        
                    if (rounding_mode):
                        v = round_to_n(v, 3)
                        
                    data[aa][bb][cc] = v
                    
                    if (v > max_value):
                        max_value = v
                    if (v < min_value):
                        min_value = v
                    
                    if (i % max(1, int(round(actual_count/nb_logs))) == 0):
                        print(str(i) + "th value is: " + str(v))
                        
                else: # 3 dim
                    vx = data[aa][bb][cc][0]
                    vy = data[aa][bb][cc][1]
                    vz = data[aa][bb][cc][2]
                    
                    if (logarithmic_mode):
                        vx = math.log10(vx)
                        vy = math.log10(vy)
                        vz = math.log10(vz)
                        
                    if (rounding_mode):
                        vx = round(vx, 2)
                        vy = round(vy, 2)
                        vz = round(vz, 2)
                        
                    if (vx > max_value):
                        max_value = vx
                    if (vx < min_value):
                        min_value = vx
                    if (vy > max_value):
                        max_value = vy
                    if (vy < min_value):
                        min_value = vy
                    if (vz > max_value):
                        max_value = vz
                    if (vz < min_value):
                        min_value = vz
                        
                    if (i % max(1, int(round(actual_count/nb_logs))) == 0):
                        log_msg = str(vx) + " " + str(vy) + " " + str(vz)
                        print(str(i) + "th row values are: " + log_msg)

    # Log computed metrics
    plural = "s" if dimensionality > 1 else ""
    print("Min value is: " + str(min_value) + " (" + str(dimensionality) + " dimension" + plural + ")")
    print("Max value is: " + str(max_value) + " (" + str(dimensionality) + " dimension" + plural + ")")
    
    # Log scanning time
    mid_time = datetime.datetime.now()
    delta = mid_time.timestamp() - start_time.timestamp()
    print("Scanned and mapped data in: " + str(round(delta, 2)) + " seconds.")
    
    # LOOP 2: normalize so it fits max resolution
    print("Normalizing " + log_ratio + str(data.size) + " (== " + str(actual_count) + ") values, parsing to hex and writing to file...")
    print("Using min_val of " + str(min_val) + ", max_val of " + str(max_val) + " and max_rez of " + str(max_rez))
    j = 0
    for a in range(0, x_range):
        for b in range(0, x_range):
            for c in range(0, z_range):
                j += step
                aa = a * step
                bb = b * step
                cc = c * step
                
                if (dimensionality == 1): # 1 dim
                    new_value = round(remap(data[aa][bb][cc], min_val, max_val, 0, max_rez, True))
                    
                    hex_value = parse_int_to_formatted_hex(new_value)
                    
                    destination_file.write(str(hex_value))
                    
                    if (j % max(1, int(round(actual_count/nb_logs))) == 0):
                        print(str(j) + "th hexadecimal value is: " + str(hex_value))
                        
                else: # 3 dim
                    new_vx = round(remap(data[aa][bb][cc][0], min_val, max_val, 0, max_rez, True))
                    new_vy = round(remap(data[aa][bb][cc][1], min_val, max_val, 0, max_rez, True))
                    new_vz = round(remap(data[aa][bb][cc][2], min_val, max_val, 0, max_rez, True))
                    
                    hex_vx = parse_int_to_formatted_hex(new_vx)
                    hex_vy = parse_int_to_formatted_hex(new_vy)
                    hex_vz = parse_int_to_formatted_hex(new_vz)
                    
                    hex_rgb = str(hex_vx) + str(hex_vy + str(hex_vz))
                    
                    destination_file.write(hex_rgb)
                    
                    if (j % max(1, int(round(actual_count/nb_logs))) == 0):
                        print(str(j) + "th hexadecimal triplet is: " + str(hex_rgb))

    # Log normalizing time
    end_time = datetime.datetime.now()
    delta = end_time.timestamp() - mid_time.timestamp()
    print("Normalized data in: " + str(round(delta, 2)) + " seconds.")
    
    # Generate Unity footer
    write_unity_footer(destination_file)
    
    # Conclude
    print("File " + destination_file_name + ".asset was created")

# Brownie B intensity
source_file = "./data/brownie_B_field_stack_01863.npy"
file_type_token = "NUMPY"
size = 237
dimensionality = 1
destination_file_name = "klodu-brown-dwarf-237"
rounding_mode = False
logarithmic_mode = False
testing_density = 1/1 # 1/1 is full rendering
nb_logs = 10
min_val = 0
max_val = 10000
max_rez = 255
# klodufy(source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)

# Brownie B lines
source_file = "./data/brownie_B_field_vector_stack_01863.npy"
file_type_token = "NUMPY"
size = 475
dimensionality = 3
rounding_mode = False
logarithmic_mode = False
testing_density = 1/1 # 1/1 is full rendering
nb_logs = 10
min_val = -10000
max_val = 10000
max_rez = 255
destination_file_name = "klodu-brown-dwarf-B-vectors-475"
# klodufy(source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)

# Dustyturb npy cloud (density)
source_file = "./data/dustyturb_density_reshaped_00524.npy"
file_type_token = "NUMPY"
size = 256
dimensionality = 1
rounding_mode = False
logarithmic_mode = False
testing_density = 1/3 # 1/1 is full rendering
nb_logs = 8
min_val = 0
max_val = 1E-18
max_rez = 255
destination_file_name = "klodu-dustyturb-256-density"
# klodufy(source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)

# Dustyturb dat cloud (density)
source_file = "./data/dustyturb_data.dat"
file_type_token = "DAT"
size = 256
dimensionality = 1
rounding_mode = False
logarithmic_mode = False
testing_density = 1/1 # 1/1 is full rendering
nb_logs = 8
min_val = 0
max_val = 50000
max_rez = 255
destination_file_name = "klodu-dustyturb-256-density"
# klodufy(source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)

# Giantclouds 00185 rho
source_file = "./data/giantclouds_00185_rho.dat"
file_type_token = "DAT"
size = 256
dimensionality = 1
rounding_mode = False
logarithmic_mode = True
testing_density = 1/5 # 1/1 is full rendering
nb_logs = 10
destination_file_name = "klodu-giantclouds-00185-256-rho"
min_val = -3
max_val = 3
max_rez = 255
# klodufy(source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)

# Giantclouds 00185 rhovx
source_file = "./data/giantclouds_00185_rhovz.dat"
file_type_token = "DAT"
size = 256
dimensionality = 1
rounding_mode = False
logarithmic_mode = False
testing_density = 1/1 # 1/1 is full rendering
nb_logs = 10
destination_file_name = "klodu-giantclouds-00185-256-rhovz"
min_val = -3000
max_val = 3000
max_rez = 255
# klodufy(source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)

# Tidalstrip .map (same as Giantcloud .dat under the hood)
source_file = "./data/tidalstrip_00236_density.map"
file_type_token = "DAT"
size = 512
dimensionality = 1
rounding_mode = False
logarithmic_mode = True
testing_density = 1/2 # 1/1 is full rendering
nb_logs = 10
min_val = 1
max_val = 10
max_rez = 255
destination_file_name = "klodu-tidalstrip-00236-512-density"
klodufy(source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)

# Tidalstrip vx
source_file = "./data/tidalstrip_00236_vz.dat"
file_type_token = "DAT"
size = 512
dimensionality = 1
rounding_mode = False
logarithmic_mode = False
testing_density = 1/10 # 1/1 is full rendering
nb_logs = 10
min_val = -5
max_val = 5
max_rez = 255
destination_file_name = "klodu-tidalstrip-00236-512-vz"
# klodufy(source_file, file_type_token, size, dimensionality, destination_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)
