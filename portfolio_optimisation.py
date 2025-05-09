import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
from scipy.optimize import minimize
from sklearn.cluster import KMeans

# Fetch historical data for given tickers
def fetch_data(tickers, start_date, end_date):
    return yf.download(tickers, start=start_date, end=end_date)['Close']

# Calculate daily returns
def calculate_returns(data):
    return data.pct_change().dropna()

# Optimize portfolio using Mean-Variance Optimization
def optimize_portfolio(returns, risk_free_rate):
    mu = returns.mean() * 252  # Annualized expected returns
    cov_matrix = returns.cov() * 252  # Annualized covariance matrix
    num_assets = len(mu)

    def sharpe_ratio(weights):
        portfolio_return = np.dot(weights, mu)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return -(portfolio_return - risk_free_rate) / portfolio_vol  # Negative for minimization

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})  # Weights sum to 1
    bounds = tuple((0, 1) for _ in range(num_assets))  # No short-selling
    initial_weights = np.ones(num_assets) / num_assets  # Equal allocation start

    result = minimize(sharpe_ratio, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.x.tolist(), -result.fun  # Return optimized weights & Sharpe ratio

# Monte Carlo simulation for portfolio optimization
def monte_carlo_simulation(returns, num_portfolios=5000, risk_free_rate=0.03):
    num_assets = len(returns.columns)
    portfolio_metrics = []

    for _ in range(num_portfolios):
        weights = np.random.dirichlet(np.ones(num_assets), size=1).flatten()
        portfolio_return = np.sum(returns.mean() * weights) * 252
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
        portfolio_metrics.append({
            "weights": weights.tolist(),
            "return": portfolio_return,
            "volatility": portfolio_volatility,
            "sharpe_ratio": sharpe_ratio
        })

    return portfolio_metrics  # JSON-friendly format

# Generate an efficient frontier plot
def plot_efficient_frontier(returns, risk_free_rate=0.03, num_portfolios=5000):
    mean_returns = returns.mean() * 252  # Annualized mean returns
    cov_matrix = returns.cov() * 252  # Annualized covariance matrix
    num_assets = len(returns.columns)

    results = {"return": [], "volatility": [], "sharpe_ratio": [], "weights": []}

    for _ in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)  # Normalize to sum to 1

        portfolio_return = np.sum(weights * mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility

        results["return"].append(portfolio_return)
        results["volatility"].append(portfolio_volatility)
        results["sharpe_ratio"].append(sharpe)
        results["weights"].append(weights.tolist())

    # Convert results to a Plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=results["volatility"], y=results["return"], mode="markers",
        marker=dict(color=results["sharpe_ratio"], colorscale="Viridis", colorbar=dict(title="Sharpe Ratio")),
        name="Portfolios"
    ))

    fig.update_layout(
        title="Efficient Frontier",
        xaxis_title="Volatility (Risk)",
        yaxis_title="Return",
        template="plotly_white"
    )

    return fig

