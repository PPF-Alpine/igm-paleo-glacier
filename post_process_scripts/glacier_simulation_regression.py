import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import seaborn as sns
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Load the data
# Update this path to match your Excel file location
file_path = "your_glacier_simulation_data.xlsx"
data = pd.read_excel(file_path)

# Display basic information about the dataset
print("Dataset overview:")
print(data.head())
print("\nDataset statistics:")
print(data.describe())

# Check for missing values
print("\nMissing values:")
print(data.isnull().sum())

# Feature engineering - create additional variables that might be relevant
data['cells'] = data['boundary_size'] / (data['spatial_resolution']**2)  # Total number of grid cells
data['total_steps'] = data['total_years_simulated'] / data['temporal_resolution']  # Total number of time steps
data['total_computations'] = data['cells'] * data['total_steps']  # Approximate total computation load

# Correlation analysis
correlation_matrix = data.corr()
print("\nCorrelation with computation time:")
print(correlation_matrix['computation_time'].sort_values(ascending=False))

# Visualize correlations
plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Matrix')
plt.savefig('correlation_matrix.png')
plt.close()

# Visualize relationships between variables and computation time
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

variables = ['boundary_size', 'spatial_resolution', 'temporal_resolution', 
             'total_years_simulated', 'cells', 'total_computations']

for i, var in enumerate(variables):
    sns.scatterplot(x=var, y='computation_time', data=data, ax=axes[i])
    axes[i].set_title(f'Computation Time vs {var}')
    # Add log-log plot inset for scaling analysis if data spans multiple orders of magnitude
    if data[var].max() / data[var].min() > 10:
        inset_ax = axes[i].inset_axes([0.6, 0.1, 0.35, 0.35])
        inset_ax.loglog(data[var], data['computation_time'], 'o', markersize=3)
        inset_ax.set_title('Log-Log Scale')

plt.tight_layout()
plt.savefig('variable_relationships.png')
plt.close()

# Prepare data for modeling
X = data[['boundary_size', 'spatial_resolution', 'temporal_resolution', 'total_years_simulated']]
y = data['computation_time']

# Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Function to build and evaluate a model
def evaluate_model(X_train, X_test, y_train, y_test, model_type="linear", poly_degree=2):
    if model_type == "polynomial":
        poly = PolynomialFeatures(degree=poly_degree)
        X_train_poly = poly.fit_transform(X_train)
        X_test_poly = poly.transform(X_test)
        
        model = LinearRegression()
        model.fit(X_train_poly, y_train)
        y_pred = model.predict(X_test_poly)
        
        # For statsmodels detailed summary
        X_train_poly_sm = sm.add_constant(X_train_poly)
        sm_model = sm.OLS(y_train, X_train_poly_sm).fit()
        
    else:  # linear model
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # For statsmodels detailed summary
        X_train_sm = sm.add_constant(X_train)
        sm_model = sm.OLS(y_train, X_train_sm).fit()
    
    # Calculate performance metrics
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n{model_type.capitalize()} Regression Model:")
    print(f"Mean Squared Error: {mse:.4f}")
    print(f"R² Score: {r2:.4f}")
    
    # Detailed statsmodels summary
    print("\nDetailed Model Summary:")
    print(sm_model.summary())
    
    # Check for multicollinearity
    if model_type == "linear":
        print("\nVariance Inflation Factors (VIF):")
        vif_data = pd.DataFrame()
        vif_data["Variable"] = X_train.columns
        vif_data["VIF"] = [variance_inflation_factor(X_train.values, i) for i in range(X_train.shape[1])]
        print(vif_data)
    
    return model, y_pred

# Evaluate linear model
linear_model, linear_preds = evaluate_model(X_train, X_test, y_train, y_test, "linear")

# Evaluate polynomial model
poly_model, poly_preds = evaluate_model(X_train, X_test, y_train, y_test, "polynomial", poly_degree=2)

# Plot actual vs predicted values
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.scatter(y_test, linear_preds)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--')
plt.xlabel('Actual Computation Time')
plt.ylabel('Predicted Computation Time')
plt.title('Linear Model: Actual vs Predicted')

plt.subplot(1, 2, 2)
plt.scatter(y_test, poly_preds)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--')
plt.xlabel('Actual Computation Time')
plt.ylabel('Predicted Computation Time')
plt.title('Polynomial Model: Actual vs Predicted')

plt.tight_layout()
plt.savefig('prediction_performance.png')
plt.close()

# Create function to predict computation time for new parameter combinations
def predict_computation_time(boundary_size, spatial_resolution, temporal_resolution, total_years_simulated, model_type="polynomial"):
    # Create a dataframe with the new parameters
    new_data = pd.DataFrame({
        'boundary_size': [boundary_size],
        'spatial_resolution': [spatial_resolution],
        'temporal_resolution': [temporal_resolution],
        'total_years_simulated': [total_years_simulated]
    })
    
    # Make prediction based on model type
    if model_type == "polynomial":
        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)  # Fit on all data
        new_data_poly = poly.transform(new_data)
        
        model = LinearRegression().fit(X_poly, y)  # Train on all data
        prediction = model.predict(new_data_poly)[0]
    else:
        model = LinearRegression().fit(X, y)  # Train on all data
        prediction = model.predict(new_data)[0]
    
    return prediction

# Example of using the prediction function
example_boundary = 100  # km²
example_spatial = 0.1   # km resolution
example_temporal = 0.01 # years
example_total_years = 100 # years

predicted_time = predict_computation_time(
    example_boundary, 
    example_spatial, 
    example_temporal, 
    example_total_years,
    model_type="polynomial"
)

print(f"\nPredicted computation time for a simulation with:")
print(f"  - Boundary size: {example_boundary} km²")
print(f"  - Spatial resolution: {example_spatial} km")
print(f"  - Temporal resolution: {example_temporal} years")
print(f"  - Total simulation time: {example_total_years} years")
print(f"Estimated computation time: {predicted_time:.2f} hours")

# Feature importance analysis
# We'll use the coefficients from the linear model as a simple measure

if hasattr(linear_model, 'coef_'):
    # Get feature importance from linear model
    importance = np.abs(linear_model.coef_)
    feature_importance = pd.DataFrame({
        'Feature': X.columns,
        'Importance': importance
    })
    feature_importance = feature_importance.sort_values('Importance', ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=feature_importance)
    plt.title('Feature Importance (Linear Model)')
    plt.tight_layout()
    plt.savefig('feature_importance.png')
    plt.close()
    
    print("\nFeature Importance (based on linear model coefficients):")
    print(feature_importance)

# Additional visualizations for insights

# Plot computation time vs the product of most important features
plt.figure(figsize=(10, 6))
if 'cells' in data.columns and 'total_steps' in data.columns:
    plt.scatter(data['cells'] * data['total_steps'], data['computation_time'])
    plt.xlabel('Cells × Total Steps')
    plt.ylabel('Computation Time')
    plt.title('Computation Time vs. Total Computational Load')
    plt.savefig('computational_load.png')
    plt.close()

print("\nAnalysis complete. Visualization files have been saved.")
