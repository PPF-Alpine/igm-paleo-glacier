import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_volume_extent_time(csv_path, time_resolution=1, polynomial_degree=3, 
                           figsize=(12, 8), save_path=None):
    """
    Plot volume and extent over time from CSV data with dual y-axes and polynomial trends.
    
    Parameters:
    -----------
    csv_path : str
        Path to the CSV file
    time_resolution : int, default=1
        Show every nth time point (1 = all points, 2 = every other point, etc.)
    polynomial_degree : int, default=3
        Degree of polynomial for trend lines
    figsize : tuple, default=(12, 8)
        Figure size (width, height)
    save_path : str, optional
        Path to save the plot (if None, only displays)
    
    Returns:
    --------
    fig, (ax1, ax2) : matplotlib figure and axes objects
    """
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_path, index_col=0)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None, None
    
    # Apply time resolution filter
    df_filtered = df.iloc[::time_resolution].copy()
    
    # Extract data
    time = df_filtered['time'].values
    volume = df_filtered['volume'].values
    extent = df_filtered['extent'].values
    
    # Remove any NaN values
    mask = ~(np.isnan(time) | np.isnan(volume) | np.isnan(extent))
    time = time[mask]
    volume = volume[mask]
    extent = extent[mask]
    
    if len(time) == 0:
        print("No valid data points found after filtering")
        return None, None
    
    # Create the plot with dual y-axes
    fig, ax1 = plt.subplots(figsize=figsize)
    ax2 = ax1.twinx()
    
    # Plot volume on left y-axis
    color1 = 'tab:blue'
    ax1.set_xlabel('Time (years)', fontsize=12)
    ax1.set_ylabel('Volume (km³)', color=color1, fontsize=12)
    line1 = ax1.plot(time, volume, color=color1, linewidth=1.5, marker='o', 
                     markersize=3, label='Volume data')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Plot extent on right y-axis
    color2 = 'tab:red'
    ax2.set_ylabel('Extent (km²)', color=color2, fontsize=12)
    line2 = ax2.plot(time, extent, color=color2, linewidth=1.5, marker='o', 
                     markersize=3, label='Extent data')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Fit and plot polynomial trends using numpy
    if len(time) > polynomial_degree:
        # Generate smooth curve for trends
        time_smooth = np.linspace(time.min(), time.max(), 300)
        
        # Fit polynomial coefficients
        volume_coeffs = np.polyfit(time, volume, polynomial_degree)
        extent_coeffs = np.polyfit(time, extent, polynomial_degree)
        
        # Generate trend lines
        volume_trend = np.polyval(volume_coeffs, time_smooth)
        extent_trend = np.polyval(extent_coeffs, time_smooth)
        
        # Plot trend lines
        ax1.plot(time_smooth, volume_trend, color=color1, linewidth=2, 
                linestyle='--', alpha=0.8, label=f'Volume trend (poly {polynomial_degree})')
        ax2.plot(time_smooth, extent_trend, color=color2, linewidth=2, 
                linestyle='--', alpha=0.8, label=f'Extent trend (poly {polynomial_degree})')
    else:
        print(f"Warning: Not enough data points for polynomial degree {polynomial_degree}")
    
    # Formatting
    plt.title(f'Volume and Extent Over Time\n(Time resolution: every {time_resolution} point(s))', 
              fontsize=14, pad=20)
    
    # Format x-axis for better readability
    ax1.ticklabel_format(style='plain', axis='x')
    
    # Add legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    # Display statistics
    print(f"Data points plotted: {len(time)}")
    print(f"Time range: {time.min():.0f} - {time.max():.0f} years")
    print(f"Volume range: {volume.min():.2f} - {volume.max():.2f} km³")
    print(f"Extent range: {extent.min():.2f} - {extent.max():.2f} km²")
    
    return fig, (ax1, ax2)

# Example usage:
if __name__ == "__main__":
    # Example usage with different time resolutions
    
    # Plot all data points
    # fig, axes = plot_volume_extent_time('your_data.csv', time_resolution=1)
    
    # Plot every 10th data point for overview of 140k years
    # fig, axes = plot_volume_extent_time('your_data.csv', time_resolution=10)
    
    # Plot every 50th data point with quadratic trend
    # fig, axes = plot_volume_extent_time('your_data.csv', time_resolution=50, polynomial_degree=2)
    
    # Save the plot
    # fig, axes = plot_volume_extent_time('your_data.csv', time_resolution=1, save_path='volume_extent_plot.png')
    
    plt.show()
