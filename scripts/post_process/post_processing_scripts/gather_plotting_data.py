

from get_ice_volume_array import get_ice_volume_with_path

def save_results_as_csv(path_to_logfile: Path, output_folder: Path):

    # get the extent area
    get_extent_area = []

    # get the volume
    ice_volume_array = get_ice_volume_with_path(path_to_logfile)

    # Combine to csv file





