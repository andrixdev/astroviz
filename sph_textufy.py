# ANDRIX x CRAL ® 2025 🤙
# 
# Generate text files with tracers data to use in Unity for the creation of 2D textures read by a VFX graph
#
# This file uses sarracen to read a PHANTOM data dump and a SHAMROCK data dump

import sarracen

# file_type_token: "PHANTOM" or "SHAMROCK"
def prepare_tracers_data (source_file, file_type_token):
    
    if (file_type_token == "PHANTOM"):
        sdf, sdf_sinks = sarracen.read_phantom(source_file)
        
        print(sdf.describe())
        
        return sdf
        
    elif (file_type_token == "SHAMROCK"):
        sdf = sarracen.read_shamrock(source_file)
        
        print(sdf.describe())
        
        return sdf
        
    else:
        print("[prepare_tracers_data(...)] Unknown file type token: " + file_type_token)
        
        return False

# Read SPH tracers particules data (positions and velocities)
def sph_textufy(source_file, destination_file_name):
    
    data = prepare_tracers_data(source_file, file_type_token)
    
    # Prepare export file
    destination_file = open("output/" + destination_file_name + ".txt", "w")
    
    # Loop into array to just output values as they are
    min_pos_value = float("inf")
    max_pos_value = float("-inf")
    min_vel_value = float("inf")
    max_vel_value = float("-inf")
    
    count = data.shape[0]
    
    print("Writing " + str(count) + " text rows to " + destination_file_name + ".txt...")
    for i in range(0, count):
        x = data.iloc[i]["x"]
        y = data.iloc[i]["y"]
        z = data.iloc[i]["z"]
        vx = data.iloc[i]["vx"]
        vy = data.iloc[i]["vy"]
        vz = data.iloc[i]["vz"]
        
        row = str(x) + " " + str(y) + " " + str(z) + " " + str(vx) + " " + str(vy) + " " + str(vz)
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
            
        if (i % 50000 == 0):
            print(str(i) + "th row is: " + row)
        
        destination_file.write(row)
        
    # Display extrema
    print("Min position value: " + str(min_pos_value))
    print("Max position value: " + str(max_pos_value))
    print("Min velocity value: " + str(min_vel_value))
    print("Max velocity value: " + str(max_vel_value))

# source_file = "./data/binarydisk_orb0m02gprev_00100"
# file_type_token = "PHANTOM"
# destination_file_name = "sph-tracers-text-binarydisk"

# source_file = "./data/disktilt_dump_0098.sham"
# file_type_token = "SHAMROCK"
# destination_file_name = "sph-tracers-text-disktilt-reduced"

source_file = "./data/disktilt_fulldump_0314.sham"
file_type_token = "SHAMROCK"
destination_file_name = "sph-tracers-text-disktilt-0314"

sph_textufy(source_file, destination_file_name)
