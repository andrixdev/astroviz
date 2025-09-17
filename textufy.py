import numpy as np
import math
import random

# Read input tracers file
def textufy (source_file, destination_file_name):
    data = np.load(source_file)
    print("Data shape is " + str(data.shape) + " with a total of " + str(data.size) + " elements.")
    
    # Prepare export file
    destination_file = open("output/" + destination_file_name + ".txt", "w")

    # Loop into array to just output values as they are
    min_pos_value = float("inf")
    max_pos_value = float("-inf")
    min_v_value = float("inf")
    max_v_value = float("-inf")
    for i in range(0, 1000):
        x = data[0][i]
        y = data[1][i]
        z = data[2][i]
        v = data[3][i]
        
        row = str(x) + " " + str(y) + " " + str(z) + " " + str(v)
        if (i < 1000 - 1):
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
        
        if (v > max_v_value):
            max_v_value = v
        if (v < min_v_value):
            min_v_value = v
        
        destination_file.write(row)
        
    # Output extrema
    print("Min position value: " + str(min_pos_value))
    print("Max position value: " + str(max_pos_value))
    print("Min intensity value: " + str(min_v_value))
    print("Max intensity value: " + str(max_v_value))

source_file = "./data/dustyturb_tracers_00524.npy"
destination_file_name = "dustyturb-tracers"

textufy(source_file, destination_file_name)
