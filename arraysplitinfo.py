import numpy as np

dir_orig = 'bigdatafiles/'
dir_splits = 'bigdatafilessplit/'
dir_dest = 'temp-and-load-sims/'

files = [
    ("extreme_simulations_fullaverageextreme_ind_p99", 5),
    ("extreme_simulations_fullaverageextreme_spatial_p99", 5),
    ("ind_simulations_70years", 16),
    ("sixstate_historical_data", 13),
    ("spatial_simulations_70years_100k", 5),
    ("spatial_simulations_70years_205k", 10),
]

def split_file_into_n(filename, n):
    # Load the large array
    large_array = np.load(dir_orig+filename+'.npy')

    # Calculate the number of elements for each smaller array
    num_parts = n
    part_size = large_array.shape[0] // num_parts

    # Split and save each part as a new file
    for i in range(num_parts):
        # Calculate the start and end indices for this part
        start_idx = i * part_size
        end_idx = start_idx + part_size if i < num_parts - 1 else large_array.shape[0]

        # Slice the array
        smaller_array = large_array[start_idx:end_idx]

        # Save the smaller array
        np.save(dir_splits+filename+'_'+str(i)+'.npy', smaller_array)
        
def check_orig_with_new(filename):
    # Load the original large array and the recombined array
    original_array = np.load(dir_orig+filename+'.npy')
    recombined_array = np.load(dir_dest+filename+'.npy')

    # Check if they are identical
    if np.array_equal(original_array, recombined_array):
        print(filename+": Success")
    else:
        print(filename+": FAILURE -- not identical")

def combine_file_from_n(filename, n):
    # Number of parts the array was split into
    num_parts = n

    # Load each smaller array and concatenate them into one large array
    recombined_array = np.concatenate([np.load(dir_splits+filename+'_'+str(i)+'.npy') for i in range(num_parts)])

    # Save the recombined array
    np.save(dir_dest+filename+'.npy', recombined_array)
