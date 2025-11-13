# ANDRIX x CRAL ® 2025 🤙
# 
# Generate text files with tracers data to use in Unity for the creation of 2D textures read by a VFX graph
#
# This file reads data dumps
# It uses sarracen to read PHANTOM and SHAMROCK dumps
# It uses numpy to read NUMPY dumps
#
# /!\ Warning: install sarracen DEVELOPMENT build
# sarracen.read_shamrock doesn't exist in stable build
# install sarracen dev build with "pip install git+https://github.com/ttricco/sarracen.git"

import math
import sarracen
import datetime
import numpy as np

# file_type_token: "PHANTOM", "SHAMROCK" or "NUMPY"
def prepare_tracers_data (source_file, file_type_token):
    
    if (file_type_token == "PHANTOM"):
        sdf, sdf_sinks = sarracen.read_phantom(source_file)
        
        print(sdf.describe())
        
        return sdf
        
    elif (file_type_token == "SHAMROCK"):
        sdf = sarracen.read_shamrock(source_file)
        
        # print(sdf.describe())
        
        return sdf
        
    elif (file_type_token == "NUMPY"):
        data = data = np.load(source_file)
        
        print("Data shape is " + str(data.shape) + " with a total of " + str(data.size) + " elements.")
        
        return data
        
    else:
        print("[prepare_tracers_data(...)] Unknown file type token: " + file_type_token)
        
        return False

def round_to_n(x, n):
    return 0 if (x == 0) else round(x, -int(math.floor(round(math.log10(abs(x)) - n + 1))))

def prepend_zeros (value, target_length):
    result = value
    size = len(str(value))
    for i in range(0, target_length - size):
        result = "0" + str(result)
        
    return result
    
def remap (input, source_min, source_max, target_min, target_max, clamp_mode):
    if (clamp_mode & (input < source_min)):
        return target_min
    elif (clamp_mode & (input > source_max)):
        return target_max
    else:
        return target_min + (target_max - target_min) * (input - source_min) / (source_max - source_min)

# Read SPH tracers particles data
def sph_textufy (source_file, file_type_token, dest_path, dest_file_name, dimensions, minmaxs, testing_density, nb_logs, skip_scanning):
    
    # Testing mode inits
    testing_density = min(1, testing_density) # Make sure it don't go krazy (> 1)
    testing_value = round(1/testing_density)
    
    # Load tracers data
    data = prepare_tracers_data(source_file, file_type_token)
    
    # Hi
    dest_file_name = dest_file_name + ("" if testing_value == 1 else ("-1-in-" + str(testing_value)))
    print("Starting work on " + dest_file_name + "...")
    
    # Prepare export file
    destination_file = open("output/" + dest_path + dest_file_name + ".txt", "w")
    
    # Get dimensions
    dims = len(dimensions)
    count = data.shape[0]
    actual_count = math.floor(count * testing_density)
    
    log_ratio = "all of " if testing_value == 1 else ("1 in " + str(testing_value) + " of all ")
    print("Writing " + log_ratio + str(count) + " (== " + str(actual_count) + ") text rows to " + dest_file_name + ".txt...")
    
    step = math.floor(testing_value)
    
    # Track time taken
    start_time = datetime.datetime.now()
    
    # LOOP 1: scan
    if (not skip_scanning):
        
        # Init scanned minmax array (extremal values of positions, velocities... whatever)
        real_minmaxs = []
        for d in range(0, dims):
            real_minmaxs.append([float("inf"), float("-inf")])
        
        # Start loop
        ii = 0
        for i in range(0, actual_count):
            ii = i * step
            
            row = ""
            
            for d in range(0, dims):
                dimension_name = dimensions[d][0]
                dimension_mode = dimensions[d][1]
                
                # Grab data value Shamrock way (dimension name)
                if (file_type_token == "SHAMROCK"):
                    # Special case for Yona's rho, derived from hpart
                    if (dimension_name == "rho"):
                        val = 1 * (data.iloc[ii]["hpart"] ** 3)
                    else:
                        val = data.iloc[ii][dimension_name]
                        
                # Grab data value Numpy way (just the order)
                elif (file_type_token == "NUMPY"):
                    val = data[ii][d]
                    
                # Checking mode
                if (dimension_mode == "log"):
                    val = math.log10(val)
                    
                # Rounding (5 digits just for the scan)
                val = round_to_n(val, 5)
                
                # Feed row to potentially print
                if (d > 0):
                    row = row + " "
                row = row + str(val)
                
                # Update max value
                if (val > real_minmaxs[d][1]):
                    real_minmaxs[d][1] = val
                    
                # Update min value
                if (val < real_minmaxs[d][0]):
                    real_minmaxs[d][0] = val
                
            if (i % max(1, int(round(actual_count/nb_logs))) == 0):
                print(str(i) + "th row is: " + row)
            
        # Log detected extrema
        for d in range(0, dims):
            dimension_name = dimensions[d][0]
            print("Min value for " + dimension_name + " is: " + str(real_minmaxs[d][0]))
            print("Max value for " + dimension_name + " is: " + str(real_minmaxs[d][1]))
            
        # Log scanning time
        mid_time = datetime.datetime.now()
        delta = mid_time.timestamp() - start_time.timestamp()
        print("Scanned and mapped data in: " + str(round(delta, 2)) + " seconds.")
    
    # LOOP 2: remap & write
    for j in range(0, actual_count):
        jj = j * step
        
        row = ""
        
        # Prepare remap
        low_quality_digits = 3
        high_quality_digits = 6
        lq_max = 10 ** low_quality_digits
        hq_max = 10 ** high_quality_digits
        
        for d in range(0, dims):
            dimension_name = dimensions[d][0]
            dimension_mode = dimensions[d][1]
            dimension_quality = dimensions[d][2]
            digits = low_quality_digits if (dimension_quality == "LQ") else high_quality_digits
            
            # Grab data value Shamrock way (dimension name)
            if (file_type_token == "SHAMROCK"):
                # Special case for Yona's rho, derived from hpart
                if (dimension_name == "rho"):
                    val = 1 * (data.iloc[jj]["hpart"] ** 3)
                else:
                    val = data.iloc[jj][dimension_name]
                    
            # Grab data value Numpy way (just the order)
            elif (file_type_token == "NUMPY"):
                val = data[jj][d]
                
            # Checking mode
            if (dimension_mode == "log"):
                val = math.log10(val)
            
            # Remap
            min_val = minmaxs[d][0]
            max_val = minmaxs[d][1]
            min_target = 0
            max_target = lq_max if (dimension_quality == "LQ") else hq_max
            val = int(round_to_n(remap(val, min_val, max_val, min_target, max_target, True), digits + 1))
            
            # Feed row to later write to file
            if (d > 0):
                row = row + " "
            row = row + str(val)
            
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
    print("File " + dest_file_name + ".txt was created")

def sph_textufy_disktilt ():
    dimensions = [ ["x", "linear", "HQ"], ["y", "linear", "HQ"], ["z", "linear", "HQ"], ["vx", "linear", "LQ"], ["vy", "linear", "LQ"], ["vz", "linear", "LQ"], ["rho", "log", "LQ"], ["soundspeed", "log", "LQ"] ]
    
    source_file = "./data/disktilt/disktilt_fulldump_0314.sham"
    file_type_token = "SHAMROCK"
    dest_path = "disktilt/test/"
    dest_file_name = "sph-disktilt-full-0314-xyzvxyzrhosound"
    minmaxs = [ [-1.8, 1.8], [-1.8, 1.8], [-1.8, 1.8], [-1E-3, 1E-3], [-1E-3, 1E-3], [-1E-3, 1E-3], [-10, -3.5], [-6.3, -5.3] ]
    testing_density = 1/100 # 1/1 is full rendering

    # source_file = "./data/disktilt/disktilt_dump_0098.sham"
    # file_type_token = "SHAMROCK"
    # dest_path = "disktilt/test/"
    # dest_file_name = "sph-disktilt-reduced-xyzvxyzrhosound"
    # minmaxs = [ [-1.8, 1.8], [-1.8, 1.8], [-1.8, 1.8], [-1E-3, 1E-3], [-1E-3, 1E-3], [-1E-3, 1E-3], [-6.5, -3.5], [-6.3, -5.3] ]
    # testing_density = 1/10 # 1/1 is full rendering
    
    nb_logs = 10
    skip_scanning = False

    sph_textufy(source_file, file_type_token, dest_path, dest_file_name, dimensions, minmaxs, testing_density, nb_logs, skip_scanning)
# sph_textufy_disktilt()

# OBSOLETE
def sph_textufy_disktilt_frame (frame, index):
    print("Generatig frame " + str(frame) + " of index " + str(index))
    
    frame_index = prepend_zeros(frame, 4)
    source_file = "./data/disktilt/99-frames/dump_" + frame_index + ".sham"
    file_type_token = "SHAMROCK"
    dest_path = "disktilt/99-frames/"
    dest_file_name = "sph-disktilt-reduced-" + frame_index
    pos_only = True
    rho_logarithmic_mode = False
    soundspeed_logarithmic_mode = False
    min_pos = -2
    max_pos = 2
    min_vel = 0
    max_vel = 0
    min_rho = 0
    max_rho = 0
    min_soundspeed = 0
    max_soundspeed = 0
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 2
    skip_scanning = True

    sph_textufy(source_file, file_type_token, dest_path, dest_file_name, pos_only, rho_logarithmic_mode, soundspeed_logarithmic_mode, min_pos, max_pos, min_vel, max_vel, min_rho, max_rho, min_soundspeed, max_soundspeed, testing_density, nb_logs, skip_scanning)
def sph_textufy_disktilt_full_99_anim():
    print("Generating 99 sph animation frames with positions...")
    
    for f in range(0, 99):
        sph_textufy_disktilt_frame(f, f)
        
    print("Generated 99 animation frames.")
# sph_textufy_disktilt_full_99_anim()

# source_file = "./data/binarydisk/binarydisk_orb0m02gprev_00100"
# file_type_token = "PHANTOM"
# dest_path = ""
# dest_file_name = "sph-binarydisk"
# prepare_tracers_data(source_file, file_type_token)

def textufy_dwarfgal ():
    dimensions = [ ["x", "linear", "HQ"], ["y", "linear", "HQ"], ["z", "linear", "HQ"], ["rho", "log", "LQ"], ["vol", "log", "LQ"], ["bx", "linear", "LQ"], ["by", "linear", "LQ"], ["bz", "linear", "LQ"], ["vx", "linear", "LQ"], ["vy", "linear", "LQ"], ["vz", "linear", "LQ"] ]
    
    source_file = "./data/dwarfgal/1-frame/data_for_alex_xyzrhovolbxbybzvxvyvz.npy"
    file_type_token = "NUMPY"
    dest_path = "dwarfgal/1-frame/"
    dest_file_name = "dwarfgal-xyzrhovolbxbybzvxvyvz"
    minmaxs = [ [-2.5, 2.5], [-2.5, 2.5], [-2.5, 2.5], [-1, 10], [-9, 3], [-600, 600], [-600, 600], [-600, 600], [-500, 500], [-500, 500], [-500, 500] ]
    testing_density = 1/1 # 1/1 is full rendering
    nb_logs = 15
    skip_scanning = False

    sph_textufy(source_file, file_type_token, dest_path, dest_file_name, dimensions, minmaxs, testing_density, nb_logs, skip_scanning)
textufy_dwarfgal()
