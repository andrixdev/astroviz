# ANDRIX x CRAL ® 2025 🤙
# 
# Generate text files with tracers data to use in Unity for the creation of 2D textures read by a VFX graph
#
# This file uses sarracen to read a PHANTOM data dump and a SHAMROCK data dump

import math
import sarracen
import datetime

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

def round_to_n(x, n):
    return round(x, -int(math.floor(round(math.log10(abs(x)) - n + 1))))

def remap (input, source_min, source_max, target_min, target_max, clamp_mode):
    if (clamp_mode & (input < source_min)):
        return target_min
    elif (clamp_mode & (input > source_max)):
        return target_max
    else:
        return target_min + (target_max - target_min) * (input - source_min) / (source_max - source_min)

# Read SPH tracers particules data (positions and velocities)
def sph_textufy (source_file, destination_file_name, rho_logarithmic_mode, soundspeed_logarithmic_mode,  pos_only, min_pos, max_pos, min_vel, max_vel, min_rho, max_rho, min_soundspeed, max_soundspeed, testing_density, nb_logs, skip_scanning):
    
    # Testing mode inits
    testing_density = min(1, testing_density) # Make sure it don't go krazy (> 1)
    testing_value = round(1/testing_density)
    
    # Load tracers data
    data = prepare_tracers_data(source_file, file_type_token)
    
    # Hi
    destination_file_name = destination_file_name + ("" if testing_value == 1 else ("-1-in-" + str(testing_value)))
    print("Starting work on " + destination_file_name + "...")
    
    # Prepare export file
    destination_file = open("output/" + destination_file_name + ".txt", "w")
    
    # Loop into array to just output values as they are
    min_pos_value = float("inf")
    max_pos_value = float("-inf")
    min_vel_value = float("inf")
    max_vel_value = float("-inf")
    min_rho_value = float("inf")
    max_rho_value = float("-inf")
    min_soundspeed_value = float("inf")
    max_soundspeed_value = float("-inf")
    
    count = data.shape[0]
    actual_count = math.floor(count * testing_density)
    testing_value = round(1/testing_density)
    
    log_ratio = "all of " if testing_value == 1 else ("1 in " + str(testing_value) + " of all ")
    print("Writing " + log_ratio + str(count) + " (== " + str(actual_count) + ") text rows to " + destination_file_name + ".txt...")
    
    step = math.floor(testing_value)
    
    # Track time taken
    start_time = datetime.datetime.now()
    
    # LOOP 1: scan
    if (not skip_scanning):
        
        ii = 0
        for i in range(0, actual_count):
            ii = i * step
            
            rho = 1 * (data.iloc[ii]["hpart"] ** 3)
            soundspeed = data.iloc[ii]["soundspeed"]
            
            if (rho_logarithmic_mode):
                rho = math.log10(rho)
            
            if (soundspeed_logarithmic_mode):
                soundspeed = math.log10(soundspeed)
            
            x = round_to_n(data.iloc[ii]["x"], 5)
            y = round_to_n(data.iloc[ii]["y"], 5)
            z = round_to_n(data.iloc[ii]["z"], 5)
            vx = round_to_n(data.iloc[ii]["vx"], 5)
            vy = round_to_n(data.iloc[ii]["vy"], 5)
            vz = round_to_n(data.iloc[ii]["vz"], 5)
            rho = round_to_n(rho, 5)
            soundspeed = round_to_n(soundspeed, 5)
            
            row = str(x) + " " + str(y) + " " + str(z) + " " + str(vx) + " " + str(vy) + " " + str(vz) + " " + str(rho) + " " + str(soundspeed)
            
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
                
            if (rho > max_rho_value):
                max_rho_value = rho
            if (rho < min_rho_value):
                min_rho_value = rho
                
            if (soundspeed > max_soundspeed_value):
                max_soundspeed_value = soundspeed
            if (soundspeed < min_soundspeed_value):
                min_soundspeed_value = soundspeed
                
            if (i % max(1, int(round(actual_count/nb_logs))) == 0):
                print(str(i) + "th row is: " + row)
            
        # Display extrema
        print("Min position value: " + str(min_pos_value))
        print("Max position value: " + str(max_pos_value))
        print("Min velocity value: " + str(min_vel_value))
        print("Max velocity value: " + str(max_vel_value))
        print("Min rho value: " + str(min_rho_value))
        print("Max rho value: " + str(max_rho_value))
        print("Min soundspeed value: " + str(min_soundspeed_value))
        print("Max soundspeed value: " + str(max_soundspeed_value))
    
        # Log scanning time
        mid_time = datetime.datetime.now()
        delta = mid_time.timestamp() - start_time.timestamp()
        print("Scanned and mapped data in: " + str(round(delta, 2)) + " seconds.")
    
    # LOOP 2: remap & write
    x = min_pos
    y = min_pos
    z = min_pos
    vx = min_vel
    vy = min_vel
    vz = min_vel
    rho = min_rho
    soundspeed = min_soundspeed
    
    for j in range(0, actual_count):
        jj = j * step
        
        min_target = 0
        max_target = 10000
        min_pos_target = 0
        max_pos_target = 1000000
        x = int(round_to_n(remap(data.iloc[jj]["x"], min_pos, max_pos, min_pos_target, max_pos_target, True), 7))
        y = int(round_to_n(remap(data.iloc[jj]["y"], min_pos, max_pos, min_pos_target, max_pos_target, True), 7))
        z = int(round_to_n(remap(data.iloc[jj]["z"], min_pos, max_pos, min_pos_target, max_pos_target, True), 7))
        
        if (not pos_only):
            vx = int(round_to_n(remap(data.iloc[jj]["vx"], min_vel, max_vel, min_target, max_target, True), 5))
            vy = int(round_to_n(remap(data.iloc[jj]["vy"], min_vel, max_vel, min_target, max_target, True), 5))
            vz = int(round_to_n(remap(data.iloc[jj]["vz"], min_vel, max_vel, min_target, max_target, True), 5))
            
            rho = 1 * (data.iloc[jj]["hpart"] ** 3)
            soundspeed = data.iloc[jj]["soundspeed"]
            
            if (rho_logarithmic_mode):
                rho = math.log10(rho)
            
            if (soundspeed_logarithmic_mode):
                soundspeed = math.log10(soundspeed)
                
            rho = int(round_to_n(remap(rho, min_rho, max_rho, min_target, max_target, True), 5))
            soundspeed = int(round_to_n(remap(soundspeed, min_soundspeed, max_soundspeed, min_target, max_target, True), 5))
        
        row = str(x) + " " + str(y) + " " + str(z)
        
        if (not pos_only):
            row = row + " " + str(vx) + " " + str(vy) + " " + str(vz) + " " + str(rho) + " " + str(soundspeed)
            
        if (j % max(1, int(round(actual_count/nb_logs))) == 0):
            print(str(j) + "th remapped row is: " + row)

        if (j < actual_count - 1):
            row += "\n"
            
        destination_file.write(row)
    
    # Log normalizing time
    end_time = datetime.datetime.now()
    delta = end_time.timestamp() - (mid_time.timestamp() if (not skip_scanning) else start_time.timestamp())
    print("Normalized data in: " + str(round(delta, 2)) + " seconds.")
    
    # Conclude
    print("File " + destination_file_name + ".txt was created")

# source_file = "./data/binarydisk_orb0m02gprev_00100"
# file_type_token = "PHANTOM"
# destination_file_name = "sph-tracers-text-binarydisk"

# source_file = "./data/disktilt/disktilt_fulldump_0314.sham"
# destination_file_name = "sph-tracers-text-disktilt-0314-rho-sound"

source_file = "./data/disktilt/disktilt_dump_0098.sham"
destination_file_name = "sph-tracers-text-disktilt-reduced-rho-sound"

file_type_token = "SHAMROCK"
rho_logarithmic_mode = True
soundspeed_logarithmic_mode = True
pos_only = True
min_pos = -2
max_pos = 2
min_vel = -1E-3
max_vel = 1E-3
min_rho = -10
max_rho = -4
min_soundspeed = -7
max_soundspeed = -5
testing_density = 1/4000 # 1/1 is full rendering
nb_logs = 10
skip_scanning = True

sph_textufy(source_file, destination_file_name, rho_logarithmic_mode, soundspeed_logarithmic_mode, pos_only, min_pos, max_pos, min_vel, max_vel, min_rho, max_rho, min_soundspeed, max_soundspeed, testing_density, nb_logs, skip_scanning)
