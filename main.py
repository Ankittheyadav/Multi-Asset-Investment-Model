from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
# from portfolio_optimisation import  optimize_portfolio
from flask import Flask, render_template, request, jsonify
from pages.portfolio_optimization import  analyze_portfolio
from pages.advance_analysis import apply_pca, risk_parity_portfolio, forecast_volatility
from pages.user_portfolio import optimize_user_portfolio
from datetime import datetime
import json
import os
import random

# Separate the import statements with newlines
app = Flask(__name__)
app.secret_key = "Ankit@2003"

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "user_login"

# MySQL Database Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ankit",
    database="Multiasset"
)
cursor = db.cursor(dictionary=True)

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_investments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        asset_type VARCHAR(50) NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        investment_date DATE NOT NULL DEFAULT (CURRENT_DATE),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")
db.commit()

# User Model for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email
        
@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (int(user_id),))
    user = cursor.fetchone()  # Returns a dictionary

    if user:
        return User(user["id"], user["username"], user["email"])  # ✅ Correct access using dictionary keys
    return None




# User Profile Page
@app.route("/profile")
@login_required
def user_profile():
    cursor.execute("SELECT * FROM user_investments WHERE user_id = %s", (current_user.id,))
    investments = cursor.fetchall()
    return render_template("profile.html", username=current_user.username, investments=investments)

# Add Investment
@app.route("/add_investment", methods=["POST"])
@login_required
def add_investment():
    asset_type = request.form["asset_type"]
    amount = float(request.form["amount"])

    cursor.execute("INSERT INTO user_investments (user_id, asset_type, amount) VALUES (%s, %s, %s)",
                   (current_user.id, asset_type, amount))
    db.commit()
    
    flash("Investment added successfully!", "success")
    return redirect(url_for("user_profile"))


# Home route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portfolio_optimization')
def portfolio_optimization():
    return render_template('portfolio_optimization.html')

@app.route('/advance_analysis')
def advance_analysis():
    return render_template('advance_analysis.html')

@app.route('/user_portfolio')
def user_portfolio():
    return render_template('user_portfolio.html')

@app.route('/analyze_portfolio', methods=['POST'])
def analyze():
    data = request.get_json()
    return analyze_portfolio(data)

@app.route('/analyze_advanced', methods=['POST'])
def analyze_advanced():
    data = request.get_json()
    tickers = data.get('tickers', '').split(',')
    start_date = data.get('start_date', '2023-01-01')
    end_date = data.get('end_date', '2024-01-01')

    try:
        pca_data, explained_variance = apply_pca(tickers, start_date, end_date)
        risk_parity = risk_parity_portfolio(tickers, start_date, end_date)
        volatility_forecast = forecast_volatility(tickers, start_date, end_date)

        return jsonify({
            "pca_results": pca_data.to_dict(),
            "explained_variance": explained_variance.tolist(),
            "risk_parity_weights": risk_parity.to_dict(),
            "volatility_forecast": volatility_forecast
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user_portfolio_analysis', methods=['POST'])
def user_portfolio_analysis():
    data = request.get_json()
    tickers = data.get('tickers', '').split(',')
    allocations = data.get('allocations', [])

    try:
        optimized_result = optimize_user_portfolio(tickers, allocations)

        return jsonify({
            "optimized_weights": optimized_result['weights'],
            "expected_return": optimized_result['expected_return'],
            "portfolio_risk": optimized_result['risk']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Username or email already exists!", "danger")  # Show error in red
            return redirect(url_for("signup"))

        # Insert new user into database
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        db.commit()  # Commit to save changes
        
        flash("Account created successfully!", "success")  # Show success message
        return redirect(url_for("user_login"))  # Stay on the signup page to show message

    return render_template("signup.html")



# Login Route
# Login Route
@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()  # Returns a dictionary

        if user and bcrypt.check_password_hash(user["password"], password):  #Use dictionary key instead of index
            user_obj = User(user["id"], user["username"], user["email"])
            login_user(user_obj)
            flash("Login successful!", "success")
            return redirect(url_for("user_profile"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("user_login"))  # Stay on the login page
    
    # Clear any remaining flash messages when rendering the login page
    session.pop('_flashes', None)
    return render_template("index.html")


# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("index"))


# Route for the Equity page - Starts Streamlit and redirects to it
@app.route('/equity')
def equity():
    return render_template("home.html")


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
    
@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        # Code inside the try block
        pass
    except Exception as e:
        # Handle the exception
        print(f"An error occurred: {e}")
        data = request.get_json()
        amount = float(data['amount'])
        years = int(data['years'])
        asset_type = data['asset_type']  # This must match what the frontend sends

        # Average growth rates for different assets (India-specific)
        growth_rates = {
            "Equity": 0.12,
            "Mutual Funds": 0.10,
            "Real Estate": 0.08,
            "Gold": 0.07,
            "Fixed Deposits": 0.06,
            "PPF": 0.075
        }

        if asset_type not in growth_rates:
            return jsonify({"error": "Invalid asset type"}), 400

        rate = growth_rates[asset_type]

        # Compound interest formula
        future_value = amount * (1 + rate) ** years
        profit = future_value - amount

        return jsonify({
            "future_value": round(future_value, 2),
            "profit": round(profit, 2)
        })

@app.route('/portfolio_analysis')
def portfolio_analysis():
    return render_template("home.html")

# Keep all your existing imports and code

# Add the real estate calculator endpoint
@app.route('/calculate_realestate', methods=['POST'])
def calculate_realestate():
    data = request.json
    
    try:
        # Extract input values
        investment_amount = float(data['amount'])
        years = int(data['years'])
        investment_type = data['type']
        location = data.get('location', 'Tier1')  # Default to Tier1 if not provided
        
        # Validate inputs
        if investment_amount <= 0:
            return jsonify({'error': 'Investment amount must be positive'})
        
        if years <= 0 or years > 30:
            return jsonify({'error': 'Investment duration must be between 1 and 30 years'})
        
        # Define annual growth rates based on investment type and location
        growth_rates = {
            'Residential': {
                'Tier1': 8.5,
                'Tier2': 9.0,
                'Tier3': 7.5
            },
            'Commercial': {
                'Tier1': 10.5,
                'Tier2': 9.5,
                'Tier3': 8.0
            },
            'Land': {
                'Tier1': 15.0,
                'Tier2': 18.0,
                'Tier3': 12.0
            },
            'REITs': {
                'Tier1': 8.0,
                'Tier2': 7.5,
                'Tier3': 7.0
            }
        }
        
        # If investment type is not found, default to Residential
        if investment_type not in growth_rates:
            investment_type = 'Residential'
            
        # Get the appropriate growth rate
        annual_rate = growth_rates[investment_type][location]
        
        # Calculate future value using compound interest formula
        future_value = investment_amount * ((1 + (annual_rate / 100)) ** years)
        profit = future_value - investment_amount
        
        # Round to integers for cleaner display
        future_value = int(future_value)
        profit = int(profit)
        
        return jsonify({
            'future_value': future_value,
            'profit': profit,
            'annual_rate': annual_rate
        })        

# Keep all your remaining code
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Path to store demo session data
DEMO_DATA_PATH = "static/demo_data/"

@app.route('/mutual_funds_demo')
def mutual_funds_demo():
    # Generate a unique session ID
    session_id = str(random.randint(100000, 999999))
    if 'demo_session_id' not in session:
        session['demo_session_id'] = session_id
        
        # Create demo data directory if it doesn't exist
        os.makedirs(DEMO_DATA_PATH, exist_ok=True)
        
        # Initialize demo account with ₹100,000
        demo_data = {
            "balance": 100000,
            "investments": [],
            "transaction_history": []
        }
        
        # Save the demo data
        with open(f"{DEMO_DATA_PATH}{session_id}.json", "w") as f:
            json.dump(demo_data, f)
    
    return render_template('mutual_funds_demo.html')

@app.route('/api/demo/account', methods=['GET'])
def get_demo_account():
    if 'demo_session_id' not in session:
        return jsonify({"error": "No demo session found"}), 404
    
    try:
        with open(f"{DEMO_DATA_PATH}{session['demo_session_id']}.json", "r") as f:
            demo_data = json.load(f)
        return jsonify(demo_data)
    except FileNotFoundError:
        return jsonify({"error": "Demo data not found"}), 404

@app.route('/api/demo/buy', methods=['POST'])
def demo_buy_fund():
    if 'demo_session_id' not in session:
        return jsonify({"error": "No demo session found"}), 404
    
    data = request.get_json()
    fund_name = data.get('fund_name')
    investment_amount = float(data.get('amount', 0))
    
    # Validate input
    if not fund_name or investment_amount <= 0:
        return jsonify({"error": "Invalid input data"}), 400
    
    try:
        # Load current demo data
        with open(f"{DEMO_DATA_PATH}{session['demo_session_id']}.json", "r") as f:
            demo_data = json.load(f)
        
        # Check if user has enough balance
        if demo_data["balance"] < investment_amount:
            return jsonify({"error": "Insufficient balance"}), 400
        
        # Create new investment
        nav = round(random.uniform(10, 150), 2)  # Random NAV between 10 and 150
        units = round(investment_amount / nav, 2)
        
        # Add investment to portfolio
        new_investment = {
            "id": len(demo_data["investments"]) + 1,
            "fund_name": fund_name,
            "amount": investment_amount,
            "units": units,
            "nav": nav,
            "purchase_date": datetime.now().strftime("%Y-%m-%d"),
            "current_value": investment_amount  # Initially the same as investment
        }
        
        # Add to portfolio and reduce balance
        demo_data["investments"].append(new_investment)
        demo_data["balance"] -= investment_amount
        
        # Add to transaction history
        demo_data["transaction_history"].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "BUY",
            "fund": fund_name,
            "amount": investment_amount,
            "units": units
        })
        
        # Save updated data
        with open(f"{DEMO_DATA_PATH}{session['demo_session_id']}.json", "w") as f:
            json.dump(demo_data, f)
        
        return jsonify({
            "success": True,
            "message": f"Successfully invested ₹{investment_amount} in {fund_name}",
            "investment": new_investment
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/demo/sell', methods=['POST'])
def demo_sell_fund():
    if 'demo_session_id' not in session:
        return jsonify({"error": "No demo session found"}), 404
    
    data = request.get_json()
    investment_id = int(data.get('investment_id', 0))
    units_to_sell = float(data.get('units', 0))
    
    # Validate input
    if investment_id <= 0 or units_to_sell <= 0:
        return jsonify({"error": "Invalid input data"}), 400
    
    try:
        # Load current demo data
        with open(f"{DEMO_DATA_PATH}{session['demo_session_id']}.json", "r") as f:
            demo_data = json.load(f)
        
        # Find the investment
        investment = None
        for inv in demo_data["investments"]:
            if inv["id"] == investment_id:
                investment = inv
                break
        
        if not investment:
            return jsonify({"error": "Investment not found"}), 404
        
        # Check if user has enough units
        if investment["units"] < units_to_sell:
            return jsonify({"error": "Not enough units to sell"}), 400
        
        # Calculate redemption amount (with a small random performance variation)
        performance_factor = random.uniform(0.95, 1.15)  # -5% to +15% performance
        current_nav = round(investment["nav"] * performance_factor, 2)
        redemption_amount = round(units_to_sell * current_nav, 2)
        
        # Update investment or remove if all units sold
        if units_to_sell >= investment["units"]:
            # Sell all
            demo_data["investments"] = [inv for inv in demo_data["investments"] if inv["id"] != investment_id]
            units_sold = investment["units"]
            fund_name = investment["fund_name"]
        else:
            # Partial sell
            for inv in demo_data["investments"]:
                if inv["id"] == investment_id:
                    inv["units"] = round(inv["units"] - units_to_sell, 2)
                    inv["amount"] = round(inv["units"] * inv["nav"], 2)
                    inv["current_value"] = inv["amount"]
                    units_sold = units_to_sell
                    fund_name = inv["fund_name"]
                    break
        
        # Add to balance
        demo_data["balance"] += redemption_amount
        
        # Add to transaction history
        demo_data["transaction_history"].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "SELL",
            "fund": fund_name,
            "amount": redemption_amount,
            "units": units_sold
        })
        
        # Save updated data
        with open(f"{DEMO_DATA_PATH}{session['demo_session_id']}.json", "w") as f:
            json.dump(demo_data, f)
        
        return jsonify({
            "success": True,
            "message": f"Successfully sold {units_sold} units for ₹{redemption_amount}",
            "amount": redemption_amount
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/demo/refresh', methods=['POST'])
def demo_refresh_portfolio():
    if 'demo_session_id' not in session:
        return jsonify({"error": "No demo session found"}), 404
    
    try:
        # Load current demo data
        with open(f"{DEMO_DATA_PATH}{session['demo_session_id']}.json", "r") as f:
            demo_data = json.load(f)
        
        # Update current values with some random variation
        for inv in demo_data["investments"]:
            performance_factor = random.uniform(0.98, 1.05)  # -2% to +5% variation
            inv["current_value"] = round(inv["amount"] * performance_factor, 2)
        
        # Save updated data
        with open(f"{DEMO_DATA_PATH}{session['demo_session_id']}.json", "w") as f:
            json.dump(demo_data, f)
        
        return jsonify({
            "success": True,
            "message": "Portfolio values updated",
            "investments": demo_data["investments"]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/demo/reset', methods=['POST'])
def demo_reset():
    if 'demo_session_id' in session:
        session_id = session['demo_session_id']
        try:
            # Delete the demo data file
            os.remove(f"{DEMO_DATA_PATH}{session_id}.json")
        except:
            pass
        
        # Remove from session
        session.pop('demo_session_id', None)
    
    return jsonify({"success": True, "message": "Demo reset successfully"})

if __name__ == '__main__':
    app.run(debug=True)
