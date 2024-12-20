
!pip install boto3
import boto3
from io import StringIO
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Load data from S3
def load_data_from_s3(bucket_name, file_key, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None):
    # Create an S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )

    # Fetch data from the S3 bucket
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    data = response['Body'].read().decode('utf-8')

    # Load data into a Pandas DataFrame
    df = pd.read_csv(StringIO(data))
    return df

## AWS credentials and S3 details (fill in your credentials)
aws_access_key_id = 'ASIAQRD5RRZGCHUL373I'
aws_secret_access_key = '2RleJ/A2ghtzcbU2YmREG0dcTuNgUKHUhqy+xeqs'
aws_session_token = 'IQoJb3JpZ2luX2VjEGMaCXVzLXdlc3QtMiJGMEQCH2EteijnaknusNHnbGgM4TcEtNmiecHkfNJ5SMl5AmQCIQDWALKYV9b6H+L4Lf45EbNXZDmGfaT7EsP7eK+Q8N3Bnyq5AggcEAAaDDAzNjc3MDUxNjU1NiIMROT88YgI/R0d+P5GKpYCLM9I0Uy5TqGObqHlHk+AzXtAKOKgjTTGL9B9IOMQd0KkmQa1wRf0wN9Xto3XZoHigP0z5tPy8Crif/lMqkvRIvf+dlUCKoQt0dwL7OgZGgZJrS8LsvQdhZkryrjW5bsA31UDusg2wHmN1CfQ9G7sJhqqSXmyiD5boWKdei6MFL8f68XA5xAcHvA2GYBdouyy5lgZg/0fLGfisQF1n5tiMbTAdY7pg1Zrtk7iICIRRiOCl6jksKtpIvaukFJEvpgAsmAj79Gj4qDfUWlBja9BGXkkjjlF21HKuxiVPpVqXZ3VdFunmkzT4owAhifIGiS33/HfTqnbr/PbRFsHERrVj9DLFRy7IxC6LoeG0ycaoVUqUx+uT3Uwg9/HugY6ngE3MxZ95XTn8soRF/8/BBIIHzTtWfb6ubwzBNjHKYhLNXmOLy2OAP36HDoe6O9Bo+0j3ROwuPydH0V1kX7r+fM8n8pJ8ShSEf3lMapYdy4SOfjXjzfPjE5QxbfEViIU6QWTpU+ZrtGUTuk+0YzZhcFUsOptvqzdlyMrZfdQeCSE2Vj/kSAeOR5FpyjYAMtxzFqZ+GVnO0qShlVnBl/5MA=='

# S3 bucket and file key
s3_bucket = "team08finalproject"
s3_file_key = "Residential.csv"
# Load data
sales = load_data_from_s3(s3_bucket, s3_file_key, aws_access_key_id, aws_secret_access_key, aws_session_token)
sales.columns= sales.columns.str.lower()
sales

sales["saledate"] = pd.to_datetime(sales["saledate"])
sales["sale_year"] = sales["saledate"].dt.year
sales["sale_month"] = sales["saledate"].dt.month
sales["sale_day"] = sales["saledate"].dt.day
#print(sales["sale_day"])

# Create a variable for the month name
month_names = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")

sales["sale_named_month"] = sales["sale_month"].map(lambda x: month_names[x-1])

# Convert to an ordered categorical variable
sales["sale_named_month"] = pd.Categorical(sales["sale_named_month"], categories = month_names, ordered = True)

sales["sale_named_month"].head()


# Create a boolean variable for if the property sold for a price over $)
sales.insert(sales.columns.get_loc("price")+1, "with_pricess", sales["price"].apply(lambda x: False if x == 0 else True))

# Create a boolean for if the property was remodeled
sales.insert(sales.columns.get_loc("yr_rmdl")+1, "remodele", sales["yr_rmdl"].notnull())

def year_diff(a, b):
    return (a.dt.year - b.year)

def month_diff(a, b):
    return 12 * (a.dt.year - b.year) + (a.dt.month - b.month)

sales["num_years_passed"] = year_diff(sales["saledate"], pd.Timestamp("2010/01/01 00:00:00+00"))
sales["num_months_passed"] = month_diff(sales["saledate"], pd.Timestamp("2010/01/01 00:00:00+00"))
sales["num_days_passed"] = (sales["saledate"] - pd.Timestamp("2010/01/01 00:00:00+00")).dt.days

year_graph_data = sales["sale_year"].value_counts().rename_axis(["sale_year"]).reset_index(name = "count")

year_graph = sns.barplot(data = year_graph_data, x = "sale_year", y = "count", color = "steelblue")
year_graph.set(title = "Number of Sales by Year", xlabel = "Year")
year_graph.set_xticks(range(0, 69, 5))
plt.show()

#print(len(sales[(sales["sale_year"] >= 2010) & (sales["sale_year"] < 2023) & sales["price"].isnull()]))

# We can add more variables this if we identify more unneeded variables
cols_to_drop = ["ssl", "gis_last_mod_dttm", "objectid"]

# We will use this dataframe for the rest of the analysis
sales_trimmed = sales[(sales["sale_year"] >= 2010) & (sales["sale_year"] < 2023) & sales["price"].notnull()].drop(cols_to_drop, axis = 1)
sales_trimmed_with_price = sales_trimmed[sales_trimmed["with_pricess"] == True]

#print(sales_trimmed_with_price)


from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Drop rows with missing values
sales_trimmed_with_price = sales_trimmed_with_price.dropna()

##  Adding num_days_passed as predictor to the model:

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(
    sales_trimmed_with_price[['bathrm', 'bedrm', 'grade', 'heat', 'cndtn', 'gba', 'num_days_passed']],
    sales_trimmed_with_price['price'],
    test_size=0.2,
    random_state=42
)

# Instantiate the linear regression model
fit5 = LinearRegression()

# Fit the model to the training data
fit5.fit(X_train, y_train)

# Make predictions on the test data
y_pred = fit5.predict(X_test)

# Evaluate the model's performance
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

from flask import Flask, render_template, request, jsonify
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np

app = Flask(__name__)

X_train, X_test, y_train, y_test = train_test_split(
    sales_trimmed_with_price[['bathrm', 'bedrm', 'grade', 'heat', 'cndtn', 'gba', 'num_days_passed']],
    sales_trimmed_with_price['price'],
    test_size=0.2,
    random_state=42
)

# Instantiate the linear regression model
fit5 = LinearRegression()

# Fit the model to the training data
fit5.fit(X_train, y_train)

# Make predictions on the test data
y_pred = fit5.predict(X_test)

feature_names=['bathrm', 'bedrm', 'grade', 'heat', 'cndtn', 'gba', 'num_days_passed']
# Define the route for the home page
@app.route('/')
def home():
    return render_template('site.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Get input features from the request
    input_data = request.form.to_dict()

    # Convert the input data to a 2D array
    input_array = np.array([float(input_data[feature]) for feature in feature_names]).reshape(1, -1)

    # Use the model to make predictions
    prediction = fit5.predict(input_array)
    print(prediction)

    # Return the prediction as a rendered HTML page
    return render_template('result.html', prediction=prediction[0])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
