from flask import Flask, render_template, request, redirect, url_for,jsonify

app = Flask(__name__)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Route for the Equity page
@app.route('/equity')
def equity():
    return render_template('equity.html')

@app.route('/mutualfunds')
def mutualfunds():
    return render_template('mutualfunds.html')

@app.route('/realestate')
def realestate():
    return render_template('realestate.html')

@app.route('/gold')
def gold():
    return render_template('gold.html')

@app.route('/fixeddeposits')
def fixeddeposits():
    return render_template('fixeddeposits.html')

@app.route('/ppf')
def ppf():
    return render_template('ppf.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login logic here
        username = request.form['username']
        password = request.form['password']
        # Add backend authentication logic
        return redirect(url_for('index'))
    return render_template('index.html')

# Route for calculating projected equity investment growth
@app.route('/calculate_investment', methods=['POST'])
def calculate_investment():
    try:
        data = request.get_json()
        amount = float(data['amount'])
        years = int(data['years'])
        annual_growth_rate = 0.12  # 12% average annual growth

        # Calculate the future value and profit
        future_value = amount * (1 + annual_growth_rate) ** years
        profit = future_value - amount
        
        return jsonify({
            "future_value": round(future_value, 2),
            "profit": round(profit, 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Route for calculating projected mutual fund investment growth
@app.route('/calculate_mutualfunds', methods=['POST'])
def calculate_mutualfunds():
    try:
        data = request.get_json()
        amount = float(data['amount'])
        years = int(data['years'])
        annual_growth_rate = 0.10  # Average annual growth rate for mutual funds

        # Calculate future value and profit
        future_value = amount * (1 + annual_growth_rate) ** years
        profit = future_value - amount  # Calculate total profit

        return jsonify({"future_value": round(future_value, 2), "profit": round(profit, 2)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

#Route for calculating Real Estate  
@app.route('/calculate_realestate', methods=['POST'])
def calculate_realestate():
    try:
        data = request.get_json()
        amount = float(data['amount'])
        years = int(data['years'])
        investment_type = data['type']

        # Define average annual growth rates
        rates = {
            'Residential': 0.08,  # 8%
            'Commercial': 0.10,   # 10%
            'Long-Term': 0.10,     # 10%
            'Rental Yields': 0.06  # 6%
        }

        annual_growth_rate = rates.get(investment_type, 0.08)  # Default to Residential if not found

        # Calculate future value and profit
        future_value = amount * (1 + annual_growth_rate) ** years
        profit = future_value - amount  # Calculate total profit

        return jsonify({"future_value": round(future_value, 2), "profit": round(profit, 2)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    #Route for calculating Gold
@app.route('/calculate_gold', methods=['POST'])
def calculate_gold():
    data = request.get_json()
    investment_amount = data['amount']
    years = data['years']
    average_return_rate = 0.11  # 11% average return

    # Calculate future value and profit
    future_value = investment_amount * (1 + average_return_rate) ** years
    profit = future_value - investment_amount

    return jsonify({
        'future_value': round(future_value, 2),
        'profit': round(profit, 2)
    })
    

#routing for calculating FDs
@app.route('/calculate_fixed_deposits', methods=['POST'])
@app.route('/calculate_fixed_deposits', methods=['POST'])
def calculate_fixed_deposits():
    data = request.json
    amount = data['amount']
    years = data['years']

    # Set interest rate based on the number of years
    if years < 1:
        interest_rate = 0.06  # 6% for less than 1 year
    elif 1 <= years <= 3:
        interest_rate = 0.07  # 7% for 1 to 3 years
    else:
        interest_rate = 0.08  # 8% for more than 3 years

    # Calculate future value and profit
    future_value = amount * (1 + interest_rate) ** years
    profit = future_value - amount

    return jsonify(future_value=future_value, profit=profit)


    
    
if __name__ == '__main__':
    app.run(debug=True)
