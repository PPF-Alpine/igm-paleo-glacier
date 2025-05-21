import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# File path for the Excel file
file_path = "igm_stats.xlsx"

# Check if the file exists
if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found.")
    print("Please make sure the Excel file is in the same directory as this script,")
    print("or update the file_path variable with the correct path.")
    sys.exit(1)

# Create output directory for generated plots if it doesn't exist
output_dir = "glacier_performance_results"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

try:
    # Load data from Excel file
    df = pd.read_excel(file_path, sheet_name='Data')
    
    # Only use specified columns
    columns_to_use = ['location', 'area', 'spatial_resolution', 'temporal_resolution', 'simulated_years', 'hours']
    
    # Check if all specified columns exist in the dataframe
    missing_columns = [col for col in columns_to_use if col not in df.columns]
    if missing_columns:
        print(f"Error: The following specified columns are missing from the Excel file: {missing_columns}")
        print(f"Found columns: {df.columns.tolist()}")
        sys.exit(1)
    
    # Filter to only use specified columns
    df = df[columns_to_use]
    
    # Print basic information about the loaded data
    print(f"Successfully loaded data from '{file_path}'")
    print(f"Number of simulation records: {len(df)}")
    print("\nSample of loaded data:")
    print(df.head())
    
    # Convert location column to string type explicitly
    df['location'] = df['location'].astype(str)
    
    # Add computation efficiency metric
    df['hours_per_year'] = df['hours'] / df['simulated_years']
    
except Exception as e:
    print(f"Error loading the Excel file: {str(e)}")
    sys.exit(1)

# 1. Location-based performance analysis
print("\n=== Location-based Performance Analysis ===")

# Calculate key metrics for each location
location_metrics = df.groupby('location').agg({
    'hours': ['mean', 'min', 'max', 'std', 'count'],
    'simulated_years': ['mean', 'min', 'max'],
    'hours_per_year': ['mean', 'min', 'max', 'std'],
    'area': ['mean'],
    'spatial_resolution': ['mean'],
    'temporal_resolution': ['mean']
})

# Flatten the multi-index columns
location_metrics.columns = ['_'.join(col).strip() for col in location_metrics.columns.values]

# Sort by average computation time
location_metrics = location_metrics.sort_values('hours_mean', ascending=False)

print("\nLocation Performance Metrics:")
print(location_metrics)

# 2. Create a summary table for export
summary_table = pd.DataFrame({
    'Location': location_metrics.index,
    'Avg Hours': location_metrics['hours_mean'],
    'Min Hours': location_metrics['hours_min'],
    'Max Hours': location_metrics['hours_max'],
    'Std Dev Hours': location_metrics['hours_std'],
    'Simulation Count': location_metrics['hours_count'],
    'Avg Simulated Years': location_metrics['simulated_years_mean'],
    'Avg Hours/Year': location_metrics['hours_per_year_mean'],
    'Avg Area': location_metrics['area_mean'],
    'Avg Spatial Resolution': location_metrics['spatial_resolution_mean'],
    'Avg Temporal Resolution': location_metrics['temporal_resolution_mean']
})

summary_table.to_excel(f"{output_dir}/location_performance_summary.xlsx", index=False)
print(f"\nLocation performance summary exported to '{output_dir}/location_performance_summary.xlsx'")

# 3. Create visualizations

# Plot 1: Average computation time by location
plt.figure(figsize=(12, 6))
ax = sns.barplot(x=location_metrics.index, y=location_metrics['hours_mean'])
plt.title('Average Computation Time by Location')
plt.xlabel('Location')
plt.ylabel('Average Computation Time (hours)')
plt.xticks(rotation=45, ha='right')
# Add value labels on top of bars
for i, v in enumerate(location_metrics['hours_mean']):
    ax.text(i, v + 0.1, f"{v:.1f}", ha='center')
plt.tight_layout()
plt.savefig(f'{output_dir}/avg_computation_time_by_location.png')
plt.close()

# Plot 2: Efficiency metric (hours per simulated year) by location
plt.figure(figsize=(12, 6))
ax = sns.barplot(x=location_metrics.index, y=location_metrics['hours_per_year_mean'])
plt.title('Computational Efficiency by Location (Hours per Simulated Year)')
plt.xlabel('Location')
plt.ylabel('Hours per Simulated Year')
plt.xticks(rotation=45, ha='right')
# Add value labels on top of bars
for i, v in enumerate(location_metrics['hours_per_year_mean']):
    ax.text(i, v + 0.05, f"{v:.2f}", ha='center')
plt.tight_layout()
plt.savefig(f'{output_dir}/efficiency_by_location.png')
plt.close()

# Plot 3: Box plot of computation times by location
plt.figure(figsize=(14, 8))
sns.boxplot(x='location', y='hours', data=df)
plt.title('Distribution of Computation Times by Location')
plt.xlabel('Location')
plt.ylabel('Computation Time (hours)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(f'{output_dir}/computation_time_boxplot.png')
plt.close()

# Plot 4: Hours vs Simulated Years scatter plot with location coloring
plt.figure(figsize=(12, 8))
sns.scatterplot(x='simulated_years', y='hours', hue='location', data=df, s=100)
plt.title('Computation Time vs Simulated Years')
plt.xlabel('Simulated Years')
plt.ylabel('Computation Time (hours)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(f'{output_dir}/hours_vs_years_by_location.png')
plt.close()

# Plot 5: Efficiency metric over simulated years
plt.figure(figsize=(12, 8))
sns.scatterplot(x='simulated_years', y='hours_per_year', hue='location', data=df, s=100)
plt.title('Computational Efficiency vs Simulated Years')
plt.xlabel('Simulated Years')
plt.ylabel('Hours per Simulated Year')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(f'{output_dir}/efficiency_vs_years_by_location.png')
plt.close()

# Plot 6: Scatter plots for each parameter vs hours
params = ['area', 'spatial_resolution', 'temporal_resolution']
for param in params:
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=param, y='hours', hue='location', data=df)
    plt.title(f'Computation Hours vs {param}')
    plt.xlabel(param)
    plt.ylabel('Computation Hours')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/hours_vs_{param}.png')
    plt.close()
    
    # Create scatter plots for each parameter vs efficiency
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=param, y='hours_per_year', hue='location', data=df)
    plt.title(f'Computational Efficiency vs {param}')
    plt.xlabel(param)
    plt.ylabel('Hours per Simulated Year')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/efficiency_vs_{param}.png')
    plt.close()

# Plot 7: Correlation heatmap for numerical columns
numeric_columns = ['area', 'spatial_resolution', 'temporal_resolution', 'simulated_years', 'hours', 'hours_per_year']
correlation = df[numeric_columns].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(correlation, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt='.2f')
plt.title('Correlation Matrix of Simulation Parameters')
plt.tight_layout()
plt.savefig(f'{output_dir}/correlation_heatmap.png')
plt.close()

# Plot 8: Pairplot for a comprehensive view of relationships
plt.figure(figsize=(12, 10))
pairs = sns.pairplot(df, vars=['area', 'spatial_resolution', 'temporal_resolution', 'simulated_years', 'hours'], 
                    hue='location')
plt.tight_layout()
pairs.savefig(f'{output_dir}/parameter_relationships_pairplot.png')
plt.close()

print(f"\nAnalysis complete. Results and visualizations saved to '{output_dir}' directory.")