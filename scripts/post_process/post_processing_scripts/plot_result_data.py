import matplotlib.pyplot as plt
import numpy as np

def plot_ice_extent_and_volume(ice_extent_areas, ice_volumes=None, time_data=None, 
                              title="Ice Extent and Volume Over Time", 
                              xlabel="Time", ylabel_area="Ice Extent Area", 
                              ylabel_volume="Ice Volume", figsize=(15, 8), 
                              save_path=None, downsample_factor=None, show_trend=True):
    """
    Plot ice extent areas and optionally ice volumes on dual y-axes.
    
    Parameters:
    -----------
    ice_extent_areas : array-like
        Array of ice extent area values
    ice_volumes : array-like, optional
        Array of ice volume values (same length as ice_extent_areas)
    time_data : array-like, optional
        Time data for x-axis. If None, uses indices.
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
    downsample_factor : int, optional
        Factor to downsample data for plotting. If None, auto-determines.
    show_trend : bool
        Whether to show trend lines
    """
    
    # Auto-determine downsampling for large datasets
    data_size = len(ice_extent_areas)
    if downsample_factor is None:
        if data_size > 50000:
            downsample_factor = max(1, data_size // 10000)
        elif data_size > 10000:
            downsample_factor = max(1, data_size // 5000)
        else:
            downsample_factor = 1
    
    # Downsample data if needed
    if downsample_factor > 1:
        indices = np.arange(0, data_size, downsample_factor)
        ice_extent_areas_plot = ice_extent_areas[indices]
        ice_volumes_plot = ice_volumes[indices] if ice_volumes is not None else None
        time_data_plot = np.array(time_data)[indices] if time_data is not None else None
    else:
        ice_extent_areas_plot = ice_extent_areas
        ice_volumes_plot = ice_volumes
        time_data_plot = time_data
    
    # Prepare x-axis data
    if time_data_plot is not None:
        x = time_data_plot
    else:
        x = np.arange(len(ice_extent_areas_plot))
    
    # Set up plotting style
    line_style = '-'
    marker_style = 'o' if data_size <= 1000 else None
    markersize = 4 if data_size <= 1000 else 0
    
    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=figsize)
    
    # Plot ice extent areas on primary axis
    color1 = 'steelblue'
    ax1.plot(x, ice_extent_areas_plot, linewidth=2, color=color1, 
             linestyle=line_style, marker=marker_style, markersize=markersize, 
             label='Ice Extent Area', alpha=0.8)
    
    ax1.set_xlabel(xlabel, fontsize=12)
    ax1.set_ylabel(ylabel_area, fontsize=12, color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Add statistics for ice extent
    mean_area = np.nanmean(ice_extent_areas)
    min_area = np.nanmin(ice_extent_areas)
    max_area = np.nanmax(ice_extent_areas)
    std_area = np.nanstd(ice_extent_areas)
    
    stats_text_area = f'Ice Extent:\nMean: {mean_area:.2f}\nMin: {min_area:.2f}\nMax: {max_area:.2f}\nStd: {std_area:.2f}'
    if downsample_factor > 1:
        stats_text_area += f'\n(Every {downsample_factor}th point)'
    
    ax1.text(0.02, 0.98, stats_text_area, transform=ax1.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Plot ice volumes on secondary axis if provided
    if ice_volumes is not None and len(ice_volumes) > 0:
        ax2 = ax1.twinx()
        color2 = 'crimson'
        
        ax2.plot(x, ice_volumes_plot, linewidth=2, color=color2, 
                 linestyle=line_style, marker=marker_style, markersize=markersize, 
                 label='Ice Volume', alpha=0.8)
        
        ax2.set_ylabel(ylabel_volume, fontsize=12, color=color2)
        ax2.tick_params(axis='y', labelcolor=color2)
        
        # Add statistics for ice volume
        mean_volume = np.nanmean(ice_volumes)
        min_volume = np.nanmin(ice_volumes)
        max_volume = np.nanmax(ice_volumes)
        std_volume = np.nanstd(ice_volumes)
        
        stats_text_volume = f'Ice Volume:\nMean: {mean_volume:.2f}\nMin: {min_volume:.2f}\nMax: {max_volume:.2f}\nStd: {std_volume:.2f}'
        if downsample_factor > 1:
            stats_text_volume += f'\n(Every {downsample_factor}th point)'
        
        ax2.text(0.98, 0.98, stats_text_volume, transform=ax2.transAxes, 
                 verticalalignment='top', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Add trend lines if requested
        if show_trend and len(x) > 10:
            # Trend for ice extent
            valid_extent = ~np.isnan(ice_extent_areas_plot)
            if np.sum(valid_extent) > 1:
                z = np.polyfit(np.arange(len(ice_extent_areas_plot))[valid_extent], 
                              ice_extent_areas_plot[valid_extent], 1)
                p = np.poly1d(z)
                ax1.plot(x, p(np.arange(len(ice_extent_areas_plot))), 
                        color=color1, linestyle="--", alpha=0.8, linewidth=2, label='Extent Trend')
            
            # Trend for ice volume
            valid_volume = ~np.isnan(ice_volumes_plot)
            if np.sum(valid_volume) > 1:
                z_vol = np.polyfit(np.arange(len(ice_volumes_plot))[valid_volume], 
                                  ice_volumes_plot[valid_volume], 1)
                p_vol = np.poly1d(z_vol)
                ax2.plot(x, p_vol(np.arange(len(ice_volumes_plot))), 
                        color=color2, linestyle="--", alpha=0.8, linewidth=2, label='Volume Trend')
        
        # Create combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')
    
    # Set title
    ax1.set_title(title, fontsize=16, fontweight='bold')
    
    # Format x-axis for readability
    if len(x) > 20:
        ax1.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    #plt.show()
