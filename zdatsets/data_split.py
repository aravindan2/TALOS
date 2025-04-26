import pandas as pd
from sklearn.model_selection import train_test_split

# Load your dataset
df = pd.read_csv('merged_ptbdb.csv')  # replace with your actual CSV file path

# Split features and target
X = df.drop('label', axis=1)  # replace 'label' with the name of your target column
y = df['label']

# Split into train and test sets (e.g., 60% train, 40% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=42)

# Optionally, merge them back to get train and test DataFrames
train_df = pd.concat([X_train, y_train], axis=1)
test_df = pd.concat([X_test, y_test], axis=1)

# Save them to CSV if needed
train_df.to_csv('train_dataset.csv', index=False)
test_df.to_csv('test_dataset.csv', index=False)
