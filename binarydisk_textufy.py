# ANDRIX x CRAL ® 2025 🤙
# 
# Generate text files with tracers data to use in Unity for the creation of 2D textures read by a VFX graph
#
# This file uses sarracen to read a PHANTOM data dump

import sarracen

def binarydisk_textufy (source_file, destination_file_name):
    sdf, sdf_sinks = sarracen.read_phantom(source_file)
    print(sdf.describe())
    
    # Prepare export file
    destination_file = open("output/" + destination_file_name + ".txt", "w")
    
    # Loop into array to just output values as they are
    min_pos_value = float("inf")
    max_pos_value = float("-inf")
    min_h_value = float("inf")
    max_h_value = float("-inf")
    count = sdf.shape[0]
    
    print("Writing values to " + destination_file_name + ".txt...")
    for i in range(0, count):
        x = sdf.iloc[i]["x"]
        y = sdf.iloc[i]["y"]
        z = sdf.iloc[i]["z"]
        h = sdf.iloc[i]["h"]
        
        row = str(x) + " " + str(y) + " " + str(z) + " " + str(h)
        if (i < count - 1):
            row += "\n"
            
        # Update minmax
        if (x > max_pos_value):
            max_pos_value = x
        if (x < min_pos_value):
            min_pos_value = x
        
        if (y > max_pos_value):
            max_pos_value = y
        if (y < min_pos_value):
            min_pos_value = y
        
        if (z > max_pos_value):
            max_pos_value = z
        if (z < min_pos_value):
            min_pos_value = z
        
        if (h > max_h_value):
            max_h_value = h
        if (h < min_h_value):
            min_h_value = h
            
        if (i % 50000 == 0):
            print(str(i) + "th row is: " + row)
        
        destination_file.write(row)
        
    # Output extrema
    print("Min position value: " + str(min_pos_value))
    print("Max position value: " + str(max_pos_value))
    print("Min h value: " + str(min_h_value))
    print("Max h value: " + str(max_h_value))
    
source_file = "./data/binarydisk_orb0m02gprev_00096"
destination_file_name = "binarydisk-tracers-text"

# binarydisk_textufy(source_file, destination_file_name)

def binarydisk_full_textufy (source_file, destination_file_name):
    sdf, sdf_sinks = sarracen.read_phantom(source_file)
    print(sdf.describe())
    
    # Prepare export file
    destination_file = open("output/" + destination_file_name + ".txt", "w")
    
    # Loop into array to just output values as they are
    min_pos_value = float("inf")
    max_pos_value = float("-inf")
    min_vel_value = float("inf")
    max_vel_value = float("-inf")
    min_h_value = float("inf")
    max_h_value = float("-inf")
    
    count = sdf.shape[0]
    
    print("Writing values to " + destination_file_name + ".txt...")
    for i in range(0, count):
        x = sdf.iloc[i]["x"]
        y = sdf.iloc[i]["y"]
        z = sdf.iloc[i]["z"]
        vx = sdf.iloc[i]["vx"]
        vy = sdf.iloc[i]["vy"]
        vz = sdf.iloc[i]["vz"]
        h = sdf.iloc[i]["h"]
        
        row = str(x) + " " + str(y) + " " + str(z) + " " + str(vx) + " " + str(vy) + " " + str(vz) + " " + str(h)
        if (i < count - 1):
            row += "\n"
            
        # Update minmax
        if (x > max_pos_value):
            max_pos_value = x
        if (x < min_pos_value):
            min_pos_value = x
        
        if (y > max_pos_value):
            max_pos_value = y
        if (y < min_pos_value):
            min_pos_value = y
        
        if (z > max_pos_value):
            max_pos_value = z
        if (z < min_pos_value):
            min_pos_value = z
            
        if (vx > max_vel_value):
            max_vel_value = vx
        if (vx < min_vel_value):
            min_vel_value = vx
            
        if (vy > max_vel_value):
            max_vel_value = vy
        if (vy < min_vel_value):
            min_vel_value = vy
            
        if (vz > max_vel_value):
            max_vel_value = vz
        if (vz < min_vel_value):
            min_vel_value = vz
        
        if (h > max_h_value):
            max_h_value = h
        if (h < min_h_value):
            min_h_value = h
            
        if (i % 50000 == 0):
            print(str(i) + "th row is: " + row)
        
        destination_file.write(row)
        
    # Output extrema
    print("Min position value: " + str(min_pos_value))
    print("Max position value: " + str(max_pos_value))
    print("Min velocity value: " + str(min_vel_value))
    print("Max velocity value: " + str(max_vel_value))
    print("Min h value: " + str(min_h_value))
    print("Max h value: " + str(max_h_value))
    

source_file = "./data/binarydisk_orb0m02gprev_00100"
destination_file_name = "binarydisk-tracers-full-text"
# binarydisk_full_textufy(source_file, destination_file_name)


# Checking the 2 rows of star data (the 2 binary stars are the sink particles!)

def check_sinks():
    sdf, sdf_sinks = sarracen.read_phantom(source_file)
    print(sdf_sinks.describe())
    x1 = sdf_sinks.iloc[0]["x"]
    y1 = sdf_sinks.iloc[0]["y"]
    z1 = sdf_sinks.iloc[0]["z"]
    x2 = sdf_sinks.iloc[1]["x"]
    y2 = sdf_sinks.iloc[1]["y"]
    z2 = sdf_sinks.iloc[1]["z"]
    print(str(x1) + " " + str(y1) + " " + str(z1))
    print(str(x2) + " " + str(y2) + " " + str(z2))

    def remap (input, source_min, source_max, target_min, target_max):
        return target_min + (target_max - target_min) * (input - source_min) / (source_max - source_min)

    x1 = remap(x1, -5600, 5600, 0, 1)
    y1 = remap(y1, -5600, 5600, 0, 1)
    z1 = remap(z1, -5600, 5600, 0, 1)
    x2 = remap(x2, -5600, 5600, 0, 1)
    y2 = remap(y2, -5600, 5600, 0, 1)
    z2 = remap(z2, -5600, 5600, 0, 1)
    print("Remapped...")
    print(str(x1) + " " + str(y1) + " " + str(z1))
    print(str(x2) + " " + str(y2) + " " + str(z2))
    
check_sinks()
