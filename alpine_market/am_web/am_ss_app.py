from flask import Flask, render_template, request, redirect, jsonify
import pandas as pd

INPUT_FILE_PATH = './am_files/mg_eq.csv'
OUTPUT_FILE_PATH = './am_files_active/aselected_scripts.csv'
app = Flask(__name__)

# Define a global variable to store the selected rows
selected_rows = pd.DataFrame()

# Define the route for the homepage
@app.route('/')
def index():
    # Read the CSV file
    df = pd.read_csv(INPUT_FILE_PATH)

    # Get column headers
    columns = df.columns.tolist()

    # Render the template with the CSV data and column headers
    return render_template('ss_index.html', data=df.to_dict(orient='records'), columns=columns)

# Define the route to handle form submission
@app.route('/process', methods=['POST'])
def process():
    global selected_rows
    selected_indices = request.form.getlist('selected')

    # Read the CSV file
    df = pd.read_csv(INPUT_FILE_PATH)

    # Filter the data based on selected indices
    selected_rows = df.iloc[[int(i) for i in selected_indices]]

    # Write selected rows to a new CSV file
    selected_rows.to_csv(OUTPUT_FILE_PATH, index=False)

    # Redirect to a success page or back to homepage
    return redirect('/success')

# Define the route for the success page
@app.route('/success')
def success():
    return f'Selected rows have been saved to {OUTPUT_FILE_PATH}'

# Define the route for pagination
@app.route('/data')
def get_data():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)

    # Read the CSV file
    df = pd.read_csv(INPUT_FILE_PATH)

    # Calculate pagination parameters
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    # Get the paginated data
    paginated_data = df.iloc[start_index:end_index].reset_index().to_dict(orient='records')

    # Return the paginated data as JSON
    return jsonify(paginated_data)

if __name__ == '__main__':
    app.run(port=5002,debug=True)