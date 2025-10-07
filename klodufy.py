# ANDRIX ® 2025 🤙
# 
# Generate 3D textures for Unity out of voxel cubes, sph tracers or pointcloud files
#
# Klodu comes from Klodo, the japanese name of Final Fantasy VII character Cloud
# Source data from CRAL - Centre de Recherche Astrophysique de Lyon

import math
import random
import os # for Fortran .dat
import numpy as np # for .npy & Fortran .dat
from scipy.io import FortranFile # for Fortran .dat
import datetime

error_start = "\033[91m"
error_end = "\033[0m"
    
def remap (input, source_min, source_max, target_min, target_max, clamp_mode):
    if (clamp_mode & (input < source_min)):
        return target_min
    elif (clamp_mode & (input > source_max)):
        return target_max
    else:
        return target_min + (target_max - target_min) * (input - source_min) / (source_max - source_min)

def write_unity_header (destination_file, file_name, base_size, testing_density, dimensionality, quality):
    
    actual_size = math.floor(base_size * testing_density)
    
    data_size_scale = 0
    encoding = ""
    
    if ((quality == "low") & (dimensionality == 1)):
        encoding = "R8"
    elif ((quality == "high") & (dimensionality == 1)):
        encoding = "R16"
    elif ((quality == "low") & (dimensionality == 3)):
        encoding = "RGB24"
    elif ((quality == "high") & (dimensionality == 3)):
        encoding = "RGB48"
        
    if (quality == "low"):
        data_size_scale = 1
    elif (quality == "high"):
        data_size_scale = 2
    else:
        print(error_start + "[write_unity_header] Error - unknown quality: " + quality + error_end)
        return None
        
    data_size = data_size_scale * dimensionality * (actual_size ** 3)
    
    # RGBAFloat -> "23"
    data_format = ""
    if (encoding == "R8"):
        data_format = "5"
    elif (encoding == "R16"):
        data_format = "21"
    elif (encoding == "RGB24"):
        data_format = "7"
    elif (encoding == "RGB48"):
        data_format = "23"
    else:
        print(error_start + "[write_unity_header] Error - unknown encoding: " + encoding + error_end)
    
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

def parse_int_to_formatted_hex (value, quality):
    # Expected format by Unity R16 tex is a bit effed-up
    # See, if color is of average intensity (min is 0000 max is ffff), you would expect something like 8803 or 88af without much difference
    # Here, Unity reads the two end characters before the two first ones, so the actual displayed intensities will be reversing the stacks of 2, so: 0388 and af88
    # Resulting in intensities of ~0% and ~70%...
    # Took me ~16h to figure it all out
    
    # Unity R8 format reads hex values in natural order (fa is almost white, 80 middle, 0e almost black)
    
    hex_value = hex(int(value))[2:] # Remove '0x' of hexadecimal notation
    
    if (quality == "high"):
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
            print(error_start + "[parse_int_to_formatted_hex] Sir we have a serious problem here, one hex value is either to short or too long! (high quality encoding)" + error_end)
            
        # Now reverse the stacks of 2 for Unity R16 & RGB48 formats
        hex_value = hex_value[2] + hex_value[3] + hex_value[0] + hex_value[1]
            
    elif (quality == "low"):
        hexlen = len(str(hex_value)) # Make sure we always have 2 characters
        if (hexlen == 1):
            hex_value = "0" + str(hex_value)
        elif (hexlen == 2):
            hex_value = hex_value
        else:
            print(error_start + "[parse_int_to_formatted_hex] Sir we have a serious problem here, one hex value is either to short or too long! (low quality encoding)" + error_end)
    
    return hex_value

def round_to_n(x, n):
    return round(x, -int(math.floor(round(math.log10(abs(x)) - n + 1))))

# Count points in pointcloud to create 3D texture (voxel cloud)
# Final texture coordinates are implict, between [0, 1] [0, 1] [0, 1], sliced into size³ cubes
# Source coordinates have to be remapped to [0, 1] [0, 1] [0, 1]
# testing_density currently doesn't work (default value of 1)
def klodufy_txt (path, size, source_min, source_max, testing_density):
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
    dimensionality = 1
    write_unity_header(destination_file, file_name, base_size, testing_density, dimensionality)
    
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
        hex_value = parse_int_to_formatted_hex(klodu[j], quality)
        
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
def klodufy_txt_bifluid ():
    source_file_name = "./data/bifluid_bin1_00045_clean3.txt"
    size = 10
    source_min = 0
    source_max = 4
    testing_density = 1/1 # Doesn't work yet
    klodufy_txt(source_file_name, size, source_min, source_max, testing_density)

# klodufy_txt_bifluid()

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
def klodufy (source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val):
    
    # Testing mode inits
    testing_density = min(1, testing_density) # Make sure it don't go krazy (> 1)
    testing_value = round(1/testing_density)
    
    # Prepare output file name
    dest_file_name = dest_file_name + ("-HQ" if quality == "high" else "-LQ")
    dest_file_name = dest_file_name + ("" if testing_value == 1 else ("-1-in-" + str(testing_value)))
    dest_file_name = dest_file_name + ("-log" if logarithmic_mode else "")
    
    # Hello
    print("Starting work on " + dest_file_name + "...")
    print("type: " + file_type_token + ", size: " + str(size) + ", dimensionality: " + str(dimensionality) + ", quality: " + quality + ", rounding mode " + ("on" if rounding_mode else "off") + ", logarithmic mode " + ("on" if logarithmic_mode else "off") + ", testing density: 1 in " + str(testing_value) + "³ == 1 in " + str(testing_value ** 3) + ", number of logs: " + str(nb_logs))
    
    # Load data cube
    data = prepare_data_cube(source_file, file_type_token)
    
    # Prepare export file
    destination_file = open("output/" + dest_path + dest_file_name + ".asset", "w")
    
    # Generate Unity header
    base_size = data.shape[0]
    base_count = base_size * base_size * base_size
    actual_count = math.floor(base_count * (testing_density ** 3))
    write_unity_header(destination_file, dest_file_name, base_size, testing_density, dimensionality, quality)
    
    # Track time taken
    start_time = datetime.datetime.now()
    
    # LOOP 1: detect extreme values, maybe round or logify
    log_ratio = "all of " if testing_value == 1 else ("1 in " + str(testing_value ** 3) + " of all ")
    print("Parsing " + log_ratio +  str(base_count) + " (== " + str(actual_count) + ") rows while scanning for min & max...")
    
    real_min_value = float("inf")
    real_max_value = float("-inf")
    
    i = 0
    logs_count = 0
    x_range = math.floor(data.shape[0] * testing_density)
    y_range = math.floor(data.shape[1] * testing_density)
    z_range = math.floor(data.shape[2] * testing_density)
    step = math.floor(data.shape[0] / x_range)
    
    for a in range(0, x_range):
        for b in range(0, x_range):
            for c in range(0, z_range):
                i += 1
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
                    
                    if (v > real_max_value):
                        real_max_value = v
                    if (v < real_min_value):
                        real_min_value = v
                    
                    if ((i / actual_count) > (logs_count / nb_logs)):
                        logs_count += 1
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
                        vx = round_to_n(vx, 3)
                        vy = round_to_n(vy, 3)
                        vz = round_to_n(vz, 3)
                        
                    if (vx > real_max_value):
                        real_max_value = vx
                    if (vx < real_min_value):
                        real_min_value = vx
                    if (vy > real_max_value):
                        real_max_value = vy
                    if (vy < real_min_value):
                        real_min_value = vy
                    if (vz > real_max_value):
                        real_max_value = vz
                    if (vz < real_min_value):
                        real_min_value = vz
                        
                    if ((i / actual_count) > (logs_count / nb_logs)):
                        logs_count += 1
                        log_msg = str(vx) + " " + str(vy) + " " + str(vz)
                        print(str(i) + "th row values are: " + log_msg)

    # Log computed metrics
    plural = "s" if dimensionality > 1 else ""
    print("Min value is: " + str(real_min_value) + " (" + str(dimensionality) + " dimension" + plural + ")")
    print("Max value is: " + str(real_max_value) + " (" + str(dimensionality) + " dimension" + plural + ")")
    
    # Log scanning time
    mid_time = datetime.datetime.now()
    delta = mid_time.timestamp() - start_time.timestamp()
    print("Scanned and mapped data in: " + str(round(delta, 2)) + " seconds.")
    
    # LOOP 2: normalize so it fits max resolution
    max_resolution = (65536 - 1) if (quality == "high") else (256 - 1)
    
    print("Normalizing " + log_ratio + str(data.size) + " (== " + str(actual_count) + ") values, parsing to hex and writing to file...")
    print("Using min_val of " + str(min_val) + ", max_val of " + str(max_val))
    j = 0
    logs_count = 0
    for a in range(0, x_range):
        for b in range(0, x_range):
            for c in range(0, z_range):
                j += 1
                aa = a * step
                bb = b * step
                cc = c * step
                
                if (dimensionality == 1): # 1 dim
                    new_value = round(remap(data[aa][bb][cc], min_val, max_val, 0, max_resolution, True))
                    
                    hex_value = parse_int_to_formatted_hex(new_value, quality)
                    
                    destination_file.write(str(hex_value))
                    
                    if ((j / actual_count) > (logs_count / nb_logs)):
                        logs_count += 1
                        print(str(j) + "th hexadecimal value is: " + str(hex_value))
                        
                else: # 3 dim
                    new_vx = round(remap(data[aa][bb][cc][0], min_val, max_val, 0, max_resolution, True))
                    new_vy = round(remap(data[aa][bb][cc][1], min_val, max_val, 0, max_resolution, True))
                    new_vz = round(remap(data[aa][bb][cc][2], min_val, max_val, 0, max_resolution, True))
                    
                    hex_vx = parse_int_to_formatted_hex(new_vx, quality)
                    hex_vy = parse_int_to_formatted_hex(new_vy, quality)
                    hex_vz = parse_int_to_formatted_hex(new_vz, quality)
                    
                    hex_rgb = str(hex_vx) + str(hex_vy) + str(hex_vz)
                    
                    destination_file.write(hex_rgb)
                    
                    if ((j / actual_count) > (logs_count / nb_logs)):
                        logs_count += 1
                        print(str(j) + "th hexadecimal triplet is: " + str(hex_rgb))

    # Log normalizing time
    end_time = datetime.datetime.now()
    delta = end_time.timestamp() - mid_time.timestamp()
    print("Normalized data in: " + str(round(delta, 2)) + " seconds.")
    
    # Generate Unity footer
    write_unity_footer(destination_file)
    
    # Conclude
    print("File " + dest_file_name + ".asset was created")

def klodufy_brownie_B_intensity ():
    source_file = "./data/brownie_B_field_stack_01863.npy"
    file_type_token = "NUMPY"
    size = 237
    dimensionality = 1
    quality = "high"
    dest_path = ""
    dest_file_name = "klo-brownie-intensity-237"
    rounding_mode = False
    logarithmic_mode = False
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 8
    min_val = 0
    max_val = 20000
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)
    
# klodufy_brownie_B_intensity()

def klodufy_brownie_B_vectors ():
    source_file = "./data/brownie_B_field_vector_stack_01863.npy"
    file_type_token = "NUMPY"
    size = 475
    dimensionality = 3
    quality = "low"
    rounding_mode = False
    logarithmic_mode = False
    testing_density = 1/25    # 1/1 is full rendering
    nb_logs = 8
    min_val = -4000
    max_val = 4000
    dest_path = ""
    dest_file_name = "klo-brownie-B-vectors-475-4000"
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)
    
# klodufy_brownie_B_vectors()

def klodufy_dustyturb_density_numpy (): # Buggy or disordered outputs
    source_file = "./data/dustyturb_density_reshaped_00524.npy"
    file_type_token = "NUMPY"
    size = 256
    dimensionality = 1
    rounding_mode = False
    logarithmic_mode = False
    testing_density = 1/37 # 1/1 is full rendering
    nb_logs = 8
    min_val = 0
    max_val = 1E-18
    max_rez = 255
    dest_path = ""
    dest_file_name = "klo-dustyturb-256-density"
    klodufy(source_file, file_type_token, size, dimensionality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val, max_rez)

# klodufy_dustyturb_density_numpy()

def klodufy_dustyturb_density ():
    source_file = "./data/dustyturb_data.dat"
    file_type_token = "DAT"
    size = 256
    dimensionality = 1
    quality = "high"
    rounding_mode = False
    logarithmic_mode = False
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 8
    min_val = 0
    max_val = 50000
    dest_path = ""
    dest_file_name = "klo-dustyturb-256-density"
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)

# klodufy_dustyturb_density()

def klodufy_giantclouds_rho ():
    source_file = "./data/giantclouds_00185_rho.dat"
    file_type_token = "DAT"
    size = 256
    dimensionality = 1
    quality = "high"
    rounding_mode = False
    logarithmic_mode = True
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 8
    dest_path = ""
    dest_file_name = "klo-giantclouds-00185-256-rho"
    min_val = -3
    max_val = 3
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)

# klodufy_giantclouds_rho()

def klodufy_giantclouds_rhovx ():
    source_file = "./data/giantclouds_00185_rhovx.dat"
    file_type_token = "DAT"
    size = 256
    dimensionality = 1
    quality = "low"
    rounding_mode = False
    logarithmic_mode = False
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 8
    dest_path = ""
    dest_file_name = "klo-giantclouds-00185-256-rhovx"
    min_val = -3000
    max_val = 3000
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)
    
# klodufy_giantclouds_rhovx()

def klodufy_tidalstrip_density ():
    source_file = "./data/tidalstrip/tidalstrip_00236_density.map" # Tidalstrip .map (same as Giantcloud .dat under the hood)
    file_type_token = "DAT"
    size = 512
    dimensionality = 1
    quality = "high"
    rounding_mode = False
    logarithmic_mode = True
    testing_density = 1/3 # 1/1 is full rendering
    nb_logs = 8
    min_val = 1
    max_val = 10
    dest_path = ""
    dest_file_name = "klo-tidalstrip-00236-512-density"
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)
    
# klodufy_tidalstrip_density()

def klodufy_tidalstrip_vx ():
    source_file = "./data/tidalstrip/tidalstrip_00236_vx.dat"
    file_type_token = "DAT"
    size = 512
    dimensionality = 1
    quality = "low"
    rounding_mode = False
    logarithmic_mode = False
    testing_density = 1/3 # 1/1 is full rendering
    nb_logs = 8
    min_val = -5
    max_val = 5
    dest_path = ""
    dest_file_name = "klo-tidalstrip-00236-512-vx"
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)

# klodufy_tidalstrip_vx()

def klodufy_outflow (source_file, file_type_token, quality, variables_index, size, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3):
    # variables_index == 1 -> x, y, z
    # variables_index == 2 -> vx, vy, vz
    # variables_index == 3 -> Bx, By, Bz
    # variables_index == 4 -> rho, cr, ⌀

    dimensionality = 3
    
    # Testing mode inits
    testing_density = min(1, testing_density) # Make sure it don't go krazy (> 1)
    testing_value = round(1/testing_density)
    
    # Prepare output file name
    dest_file_name = dest_file_name + ("-HQ" if quality == "high" else "-LQ")
    dest_file_name = dest_file_name + ("" if testing_value == 1 else ("-1-in-" + str(testing_value)))
    dest_file_name = dest_file_name + ("-log" if logarithmic_mode else "")
    
    # Hello
    print("Starting work on " + dest_file_name + "...")
    print("variables_index: " + str(variables_index) + ", type: " + file_type_token + ", size: " + str(size) + ", rounding mode " + ("on" if rounding_mode else "off") + ", logarithmic mode " + ("on" if logarithmic_mode else "off") + ", testing density: 1 in " + str(testing_value) + ", number of logs: " + str(nb_logs))
    
    # Load data cube
    data = prepare_data_cube(source_file, file_type_token)
    
    # Prepare export file
    destination_file = open("output/" + dest_path + dest_file_name + ".asset", "w")
    
    # Generate Unity header
    base_size = int(math.floor(data.shape[1] ** (1/3)))
    base_count = base_size * base_size * base_size
    actual_count = math.floor(base_count * testing_density)
    write_unity_header(destination_file, dest_file_name, base_size, testing_density, dimensionality, quality)
    
    # Track time taken
    start_time = datetime.datetime.now()
    
    # LOOP 1: detect extreme values, maybe round or logify
    log_ratio = "all of " if testing_value == 1 else ("1 in " + str(testing_value) + " of all ")
    print("Parsing " + log_ratio + str(base_count) + " (== " + str(actual_count) + ") values while scanning for min & max...")
    
    real_min_v1 = float("inf")
    real_max_v1 = float("-inf")
    real_min_v2 = float("inf")
    real_max_v2 = float("-inf")
    real_min_v3 = float("inf")
    real_max_v3 = float("-inf")
    
    logs_count = 0
    for_range = math.floor(base_count * testing_density)
    step = math.floor(base_count / for_range)
    v1_index = 3 * (variables_index - 1) + 0
    v2_index = 3 * (variables_index - 1) + 1
    v3_index = 3 * (variables_index - 1) + 2
    
    for i in range(0, for_range):
        ii = i * step
        v1 = 0
        v2 = 0
        v3 = 0
        
        # Get the right variables (x y z, vx vy vz, Bx By Bz, or cr rho ⌀)
        v1 = data[v1_index][ii]
        if (v2_index < 11):
            v2 = data[v2_index][ii]
        if (v3_index < 11):
            v3 = data[v3_index][ii]
            
        if (logarithmic_mode):
            v1 = math.log10(max(1E-30, v1))
            v2 = math.log10(max(1E-30, v2))
            v3 = math.log10(max(1E-30, v3))
            
        if (rounding_mode):
            v1 = round_to_n(v1, 3)
            v2 = round_to_n(v2, 3)
            v3 = round_to_n(v3, 3)
            
        if (v1 > real_max_v1):
            real_max_v1 = v1
        if (v1 < real_min_v1):
            real_min_v1 = v1
        if (v2 > real_max_v2):
            real_max_v2 = v2
        if (v2 < real_min_v2):
            real_min_v2 = v2
        if (v3 > real_max_v3):
            real_max_v3 = v3
        if (v3 < real_min_v3):
            real_min_v3 = v3
            
        if ((i / actual_count) > (logs_count / nb_logs)):
            logs_count += 1
            log_msg = str(v1) + " " + str(v2) + " " + str(v3)
            print(str(i) + "th row values are: " + log_msg)
                        
    # Log computed metrics
    print("Data min values are: " + str(real_min_v1) + " " + str(real_min_v2) + " " + str(real_min_v3))
    print("Data max values are: " + str(real_max_v1) + " " + str(real_max_v2) + " " + str(real_max_v3))
    
    # Log scanning time
    mid_time = datetime.datetime.now()
    delta = mid_time.timestamp() - start_time.timestamp()
    print("Scanned and mapped data in: " + str(round(delta, 2)) + " seconds.")
    
    # LOOP 2: normalize so it fits max resolution
    max_resolution = (65536 - 1) if (quality == "high") else (256 - 1)
    
    print("Normalizing " + log_ratio + str(base_count) + " (== " + str(actual_count) + ") values, parsing to hex and writing to file...")
    print("Using mins of " + str(min_v1) + " " + str(min_v2) + " " + str(min_v3) + " & maxs of " + str(max_v1) + " " + str(max_v2) + " " + str(max_v3))
    
    logs_count = 0
    for j in range(0, for_range):
        jj = j * step
        v1 = 0
        v2 = 0
        v3 = 0
        
        # Get the right variables (x y z, vx vy vz, Bx By Bz, or cr rho ⌀)
        v1 = data[v1_index][jj]
        if (v2_index < 11):
            v2 = data[v2_index][jj]
        if (v3_index < 11):
            v3 = data[v3_index][jj]
            
        if (logarithmic_mode):
            v1 = math.log10(max(1E-30, v1))
            v2 = math.log10(max(1E-30, v2))
            v3 = math.log10(max(1E-30, v3))
            
        if (rounding_mode):
            v1 = round_to_n(v1, 6)
            v2 = round_to_n(v2, 6)
            v3 = round_to_n(v3, 6)
            
        new_v1 = round(remap(v1, min_v1, max_v1, 0, max_resolution, True))
        new_v2 = round(remap(v2, min_v2, max_v2, 0, max_resolution, True))
        new_v3 = round(remap(v3, min_v3, max_v3, 0, max_resolution, True))
        
        hex_v1 = parse_int_to_formatted_hex(new_v1, quality)
        hex_v2 = parse_int_to_formatted_hex(new_v2, quality)
        hex_v3 = parse_int_to_formatted_hex(new_v3, quality)
        
        hex_rgb = str(hex_v1) + str(hex_v2) + str(hex_v3)
        
        destination_file.write(hex_rgb)
        
        if ((j / actual_count) > (logs_count / nb_logs)):
            logs_count += 1
            print(str(j) + "th hexadecimal value is: " + str(hex_rgb))
    
    # Log normalizing time
    end_time = datetime.datetime.now()
    delta = end_time.timestamp() - mid_time.timestamp()
    print("Normalized data in: " + str(round(delta, 2)) + " seconds.")
    
    # Generate Unity footer
    write_unity_footer(destination_file)
    
    # Conclude
    print("File " + dest_file_name + ".asset was created")

def klodufy_outflow_values (zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode):
    file_type_token = "NUMPY"
    size = 256
    rounding_mode = False
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 3
    source_file = "./data/outflow_1M_isolated_collapse_" + str(zoom) + "AU.npy"
    dest_path = ""
    dest_file_name = "klo-outflow-" +  str(zoom) + "-var" + str(variables_index)
    klodufy_outflow(source_file, file_type_token, quality, variables_index, size, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3)

def klodufy_outflow_8000au_positions ():
    zoom = 8000
    variables_index = 1
    quality = "high"
    logarithmic_mode = False
    min_v1 = -1.2E17
    max_v1 = 1.2E17
    min_v2 = -1.2E17
    max_v2 = 1.2E17
    min_v3 = -1.2E17
    max_v3 = 1.2E17
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_8000au_velocities ():
    zoom = 8000
    variables_index = 2
    quality = "low"
    logarithmic_mode = False
    min_v1 = -4E5
    max_v1 = 4E5
    min_v2 = -4E5
    max_v2 = 4E5
    min_v3 = -4E5
    max_v3 = 4E5
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_8000au_B_vectors ():
    zoom = 8000
    variables_index = 3
    quality = "low"
    logarithmic_mode = False
    min_v1 = -0.03
    max_v1 = 0.03
    min_v2 = -0.03
    max_v2 = 0.03
    min_v3 = -0.03
    max_v3 = 0.03
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_8000au_rho_cr ():
    zoom = 8000
    variables_index = 4
    quality = "high"
    logarithmic_mode = True
    min_v1 = -20
    max_v1 = -10
    min_v2 = -16
    max_v2 = -2
    min_v3 = 0
    max_v3 = 1
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_1000au_positions ():
    zoom = 1000
    variables_index = 1
    quality = "high"
    logarithmic_mode = False
    min_v1 = -1E16
    max_v1 = 1E16
    min_v2 = -1E16
    max_v2 = 1E16
    min_v3 = -1E16
    max_v3 = 1E16
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_1000au_velocities ():
    zoom = 1000
    variables_index = 2
    quality = "low"
    logarithmic_mode = False
    min_v1 = -4E5
    max_v1 = 4E5
    min_v2 = -4E5
    max_v2 = 4E5
    min_v3 = -4E5
    max_v3 = 4E5
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_1000au_B_vectors ():
    zoom = 1000
    variables_index = 3
    quality = "low"
    logarithmic_mode = False
    min_v1 = -0.04
    max_v1 = 0.04
    min_v2 = -0.04
    max_v2 = 0.04
    min_v3 = -0.04
    max_v3 = 0.04
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_1000au_rho_cr ():
    zoom = 1000
    variables_index = 4
    quality = "high"
    logarithmic_mode = True
    min_v1 = -17.5
    max_v1 = -10
    min_v2 = -15
    max_v2 = -2
    min_v3 = 0
    max_v3 = 1
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_100au_positions ():
    zoom = 100
    variables_index = 1
    quality = "high"
    logarithmic_mode = False
    min_v1 = -8E14
    max_v1 = 8E14
    min_v2 = -8E14
    max_v2 = 8E14
    min_v3 = -8E14
    max_v3 = 8E14
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_100au_velocities ():
    zoom = 100
    variables_index = 2
    quality = "low"
    logarithmic_mode = False
    min_v1 = -4E5
    max_v1 = 4E5
    min_v2 = -4E5
    max_v2 = 4E5
    min_v3 = -4E5
    max_v3 = 4E5
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_100au_B_vectors ():
    zoom = 100
    variables_index = 3
    quality = "low"
    logarithmic_mode = False
    min_v1 = -0.04
    max_v1 = 0.04
    min_v2 = -0.04
    max_v2 = 0.04
    min_v3 = -0.04
    max_v3 = 0.04
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)
def klodufy_outflow_100au_rho_cr ():
    zoom = 100
    variables_index = 4
    quality = "high"
    logarithmic_mode = True
    min_v1 = -17.1
    max_v1 = -10
    min_v2 = -15
    max_v2 = -2
    min_v3 = 0
    max_v3 = 1
    
    klodufy_outflow_values(zoom, variables_index, quality, min_v1, max_v1, min_v2, max_v2, min_v3, max_v3, logarithmic_mode)

# klodufy_outflow_8000au_positions()
# klodufy_outflow_8000au_velocities()
# klodufy_outflow_8000au_B_vectors()
# klodufy_outflow_8000au_rho_cr()
# klodufy_outflow_1000au_positions()
# klodufy_outflow_1000au_velocities()
# klodufy_outflow_1000au_B_vectors()
# klodufy_outflow_1000au_rho_cr()
# klodufy_outflow_100au_positions()
# klodufy_outflow_100au_velocities()
# klodufy_outflow_100au_B_vectors()
# klodufy_outflow_100au_rho_cr()

def klodufy_tidalstrip_anim_vel (frame, vel_type):
    file_end = tidal_frame_to_file_end(frame)
    source_file = "./data/tidalstrip/tidal_" + vel_type + "_128_" + file_end + ".dat"
    file_type_token = "DAT"
    size = 128
    dimensionality = 1
    quality = "low"
    rounding_mode = False
    logarithmic_mode = False
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 8
    min_val = -5
    max_val = 5
    dest_path = "tidalstrip/5-frames/"
    dest_file_name = "klo-tidal-" + vel_type + "-128-anim-" + str(frame)
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)

# klodufy_tidalstrip_anim_vel(1, "vx")
# klodufy_tidalstrip_anim_vel(2, "vx")
# klodufy_tidalstrip_anim_vel(3, "vx")
# klodufy_tidalstrip_anim_vel(4, "vx")
# klodufy_tidalstrip_anim_vel(5, "vx")
# klodufy_tidalstrip_anim_vel(1, "vy")
# klodufy_tidalstrip_anim_vel(2, "vy")
# klodufy_tidalstrip_anim_vel(3, "vy")
# klodufy_tidalstrip_anim_vel(4, "vy")
# klodufy_tidalstrip_anim_vel(5, "vy")
# klodufy_tidalstrip_anim_vel(1, "vz")
# klodufy_tidalstrip_anim_vel(2, "vz")
# klodufy_tidalstrip_anim_vel(3, "vz")
# klodufy_tidalstrip_anim_vel(4, "vz")
# klodufy_tidalstrip_anim_vel(5, "vz")

def klodufy_tidalstrip_anim_density (frame, index):
    source_file = "./data/tidalstrip/51-frames/density_output00" + str(frame) + "_GID0009_res128.dat"
    file_type_token = "DAT"
    size = 128
    dimensionality = 1
    quality = "high"
    rounding_mode = False
    logarithmic_mode = True
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 2
    min_val = 1
    max_val = 10
    dest_path = "tidalstrip/32-frames/"
    dest_file_name = "klo-tidal-density-128-anim-" + str(index)
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)
    
def klodufy_tidalstrip_full_32_anim ():
    times = np.loadtxt("./data/tidalstrip/51-frames/filtered_times_only_32.txt")
    size = len(times)
    # print("Generating " + str(size) + " animation frames with density, vx, vy, and vz (" + 4 * size + " klodus in total)")
    print("Generating " + str(size) + " animation frames with density (" + str(1 * size) + " klodus in total)...")
    
    for t in range(0, size):
        time = int(times[t][0])
        klodufy_tidalstrip_anim_density(time, t + 1)
        
    print("Generated " + str(size) + " animation frames.")
    
# klodufy_tidalstrip_full_32_anim()

def klodufy_giantclouds_anim_rho (frame, index):
    print(frame)
    print(index)
    
    source_file = "./data/giantclouds/17-frames/cube_cloud_rho_output_00" + str(frame) + ".dat"
    file_type_token = "DAT"
    size = 256
    dimensionality = 1
    quality = "low"
    rounding_mode = False
    logarithmic_mode = True
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 2
    min_val = -3.5
    max_val = 3.5
    dest_path = "giantclouds/17-frames/"
    dest_file_name = "klo-giantclouds-rho-256-anim-" + str(index)
    klodufy(source_file, file_type_token, size, dimensionality, quality, dest_path, dest_file_name, rounding_mode, logarithmic_mode, testing_density, nb_logs, min_val, max_val)
        
def klodufy_giantclouds_full_17_anim ():
    print("Generating 17 animation frames with density (17 klodus in total)...")
    
    for f in range(172, 188 + 1):
        klodufy_giantclouds_anim_rho(f, 1 + f - 172)
        
    print("Generated 17 animation frames.")
    
klodufy_giantclouds_full_17_anim()
