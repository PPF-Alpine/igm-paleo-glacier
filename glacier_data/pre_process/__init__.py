# Import from clip module
from .clip.clip_atmosphere_to_bounds import save_clipped_atmosphere
from .clip.clip_bootstrap_to_bounds import save_clipped_bootstrap
from .clip.clip_polygon import (
    save_clipped_atmosphere_with_polygon,
    save_clipped_bootstrap_with_polygon
)

# Import from download module
from .download import download_chelsa
from .download import download_and_extract_gebco
from .download import download_and_extract_pbcor
from .download import download_epica, epica_to_netcdf
