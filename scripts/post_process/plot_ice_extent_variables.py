import matplotlib.pyplot as plt
import numpy as np

def plot_ice_extent_and_volume(ice_extent_areas, ice_volumes=None, time_data=None, 
                         title="Ice Extent and Volume Over Time", 
                         xlabel="Time", ylabel_area="Ice Extent Area", 
                         ylabel_volume="Ice Volume", figsize=(12, 8), save_path=None):
    """
    Plot ice extent areas and optionally ice volumes as a time series.
    
    Parameters: 
    -----------
    ice_extent_areas : array-like
        Array of ice extent area values
    ice_volumes : array-like, optional
        Array of ice volume values (same length as ice_extent_areas)
    time_data : array-like, optional
        Time data (years, dates, etc.) for x-axis. If None, uses indices.
    title : str
        Plot title
    xlabel : str
        X-axis label
    ylabel_area : str
        Y-axis label for ice extent area
    ylabel_volume : str
        Y-axis label for ice volume
    figsize : tuple
        Figure size (width, height)
    save_path : str, optional
        Path to save the plot. If None, plot is shown but not saved.
    """
    
    # Determine if we're plotting one or two variables
    plot_volume = ice_volumes is not None
    
    if plot_volume:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        axes = [ax1, ax2]
    else:
        fig, ax1 = plt.subplots(figsize=figsize)
        axes = [ax1]
    
    # Create x-axis data
    if time_data is not None:
        x = time_data
    else:
        x = np.arange(len(ice_extent_areas))
    
    # Plot ice extent areas
    ax1.plot(x, ice_extent_areas, linewidth=2, color='steelblue', marker='o', markersize=4, label='Ice Extent Area')
    ax1.set_ylabel(ylabel_area, fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Add statistics for ice extent
    mean_area = np.mean(ice_extent_areas)
    min_area = np.min(ice_extent_areas)
    max_area = np.max(ice_extent_areas)
    
    stats_text_area = f'Mean: {mean_area:.2f}\nMin: {min_area:.2f}\nMax: {max_area:.2f}'
    ax1.text(0.02, 0.98, stats_text_area, transform=ax1.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Plot ice volumes if provided
    if plot_volume:
        ax2.plot(x, ice_volumes, linewidth=2, color='crimson', marker='s', markersize=4, label='Ice Volume')
        ax2.set_ylabel(ylabel_volume, fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Add statistics for ice volume
        mean_volume = np.mean(ice_volumes)
        min_volume = np.min(ice_volumes)
        max_volume = np.max(ice_volumes)
        
        stats_text_volume = f'Mean: {mean_volume:.2f}\nMin: {min_volume:.2f}\nMax: {max_volume:.2f}'
        ax2.text(0.02, 0.98, stats_text_volume, transform=ax2.transAxes, 
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Set title and x-label
    if plot_volume:
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax2.set_xlabel(xlabel, fontsize=12)
    else:
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_xlabel(xlabel, fontsize=12)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    plt.show()

