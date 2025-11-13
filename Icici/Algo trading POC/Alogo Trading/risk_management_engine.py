"""
Advanced Risk Management and Portfolio Optimization Engine
Implements sophisticated risk metrics and portfolio theory for NIFTY trading
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskManagementEngine:
    """Advanced Risk Management Engine for portfolio optimization"""
    
    def __init__(self):
        self.price_history = []
        self.portfolio_positions = []
        self.risk_metrics_cache = {}
        self.var_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        
    def add_price_data(self, price, timestamp=None, volume=0):
        """Add price data for risk calculations"""
        if timestamp is None:
            timestamp = datetime.now()
            
        price_point = {
            'price': float(price),
            'timestamp': timestamp,
            'volume': float(volume)
        }
        
        self.price_history.append(price_point)
        
        # Keep last 500 points for risk analysis
        if len(self.price_history) > 500:
            self.price_history = self.price_history[-500:]
    
    def add_position(self, symbol, shares, entry_price, entry_time=None, stop_loss=None, take_profit=None):
        """Add a trading position to portfolio"""
        if entry_time is None:
            entry_time = datetime.now()
            
        position = {
            'symbol': symbol,
            'shares': int(shares),
            'entry_price': float(entry_price),
            'entry_time': entry_time,
            'stop_loss': float(stop_loss) if stop_loss else None,
            'take_profit': float(take_profit) if take_profit else None,
            'position_value': shares * entry_price,
            'unrealized_pnl': 0,
            'max_drawdown': 0,
            'peak_value': shares * entry_price
        }
        
        self.portfolio_positions.append(position)
        logger.info(f"📊 Added position: {shares} shares of {symbol} at ₹{entry_price}")
    
    def calculate_var(self, confidence_level=0.95, time_horizon=1):
        """Calculate Value at Risk (VaR) using historical simulation"""
        try:
            if len(self.price_history) < 30:
                return {'var': 0, 'expected_shortfall': 0, 'method': 'insufficient_data'}
            
            prices = [p['price'] for p in self.price_history]
            
            # Calculate returns
            returns = np.diff(prices) / prices[:-1]
            
            # Historical VaR
            var_percentile = (1 - confidence_level) * 100
            historical_var = np.percentile(returns, var_percentile)
            
            # Expected Shortfall (Conditional VaR)
            tail_returns = returns[returns <= historical_var]
            expected_shortfall = np.mean(tail_returns) if len(tail_returns) > 0 else historical_var
            
            # Parametric VaR (assuming normal distribution)
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            z_score = stats.norm.ppf(1 - confidence_level)
            parametric_var = mean_return + z_score * std_return
            
            # Monte Carlo VaR simulation
            mc_var = self._monte_carlo_var(returns, confidence_level, time_horizon)
            
            return {
                'historical_var': round(historical_var * 100, 3),  # Convert to percentage
                'parametric_var': round(parametric_var * 100, 3),
                'monte_carlo_var': round(mc_var * 100, 3),
                'expected_shortfall': round(expected_shortfall * 100, 3),
                'confidence_level': confidence_level,
                'time_horizon': time_horizon,
                'volatility': round(std_return * 100 * np.sqrt(252), 2),  # Annualized
                'mean_return': round(mean_return * 100 * 252, 2)  # Annualized
            }
            
        except Exception as e:
            logger.error(f"❌ VaR calculation error: {e}")
            return {'var': 0, 'expected_shortfall': 0, 'method': 'error'}
    
    def _monte_carlo_var(self, returns, confidence_level, time_horizon, num_simulations=1000):
        """Monte Carlo simulation for VaR calculation"""
        try:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            # Generate random scenarios
            random_returns = np.random.normal(mean_return, std_return, num_simulations * time_horizon)
            scenario_returns = random_returns.reshape(num_simulations, time_horizon)
            
            # Calculate cumulative returns for each scenario
            cumulative_returns = np.prod(1 + scenario_returns, axis=1) - 1
            
            # Calculate VaR
            var_percentile = (1 - confidence_level) * 100
            mc_var = np.percentile(cumulative_returns, var_percentile)
            
            return mc_var
            
        except Exception as e:
            logger.error(f"❌ Monte Carlo VaR error: {e}")
            return 0
    
    def calculate_sharpe_ratio(self, risk_free_rate=0.06):
        """Calculate Sharpe ratio for the trading strategy"""
        try:
            if len(self.price_history) < 10:
                return {'sharpe_ratio': 0, 'excess_return': 0, 'volatility': 0}
            
            prices = [p['price'] for p in self.price_history]
            returns = np.diff(prices) / prices[:-1]
            
            # Annualized metrics
            annual_return = np.mean(returns) * 252
            annual_volatility = np.std(returns) * np.sqrt(252)
            
            # Excess return over risk-free rate
            excess_return = annual_return - risk_free_rate
            
            # Sharpe ratio
            sharpe_ratio = excess_return / annual_volatility if annual_volatility > 0 else 0
            
            return {
                'sharpe_ratio': round(sharpe_ratio, 3),
                'annual_return': round(annual_return * 100, 2),
                'annual_volatility': round(annual_volatility * 100, 2),
                'excess_return': round(excess_return * 100, 2),
                'risk_free_rate': round(risk_free_rate * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Sharpe ratio calculation error: {e}")
            return {'sharpe_ratio': 0, 'excess_return': 0, 'volatility': 0}
    
    def calculate_maximum_drawdown(self):
        """Calculate maximum drawdown from price history"""
        try:
            if len(self.price_history) < 2:
                return {'max_drawdown': 0, 'drawdown_duration': 0, 'recovery_time': 0}
            
            prices = [p['price'] for p in self.price_history]
            
            # Calculate cumulative maximum (peak values)
            cummax = np.maximum.accumulate(prices)
            
            # Calculate drawdown
            drawdown = (prices - cummax) / cummax
            
            # Maximum drawdown
            max_drawdown = np.min(drawdown)
            
            # Find drawdown periods
            drawdown_periods = []
            start_dd = None
            
            for i, dd in enumerate(drawdown):
                if dd < 0 and start_dd is None:
                    start_dd = i
                elif dd == 0 and start_dd is not None:
                    drawdown_periods.append(i - start_dd)
                    start_dd = None
            
            # Average drawdown duration
            avg_dd_duration = np.mean(drawdown_periods) if drawdown_periods else 0
            
            # Current drawdown
            current_drawdown = drawdown[-1]
            
            return {
                'max_drawdown': round(max_drawdown * 100, 3),
                'current_drawdown': round(current_drawdown * 100, 3),
                'avg_drawdown_duration': round(avg_dd_duration, 1),
                'num_drawdown_periods': len(drawdown_periods),
                'recovery_factor': round(abs(max_drawdown) / np.std(drawdown), 2) if np.std(drawdown) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Maximum drawdown calculation error: {e}")
            return {'max_drawdown': 0, 'drawdown_duration': 0, 'recovery_time': 0}
    
    def calculate_beta(self, market_returns=None):
        """Calculate beta relative to market (NIFTY)"""
        try:
            if len(self.price_history) < 20:
                return {'beta': 1.0, 'correlation': 0, 'alpha': 0}
            
            prices = [p['price'] for p in self.price_history]
            asset_returns = np.diff(prices) / prices[:-1]
            
            # If no market returns provided, assume NIFTY benchmark
            if market_returns is None:
                # Generate synthetic market returns for demonstration
                market_returns = asset_returns * 0.8 + np.random.normal(0, 0.005, len(asset_returns))
            
            # Calculate beta
            covariance = np.cov(asset_returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)
            beta = covariance / market_variance if market_variance > 0 else 1.0
            
            # Calculate correlation
            correlation = np.corrcoef(asset_returns, market_returns)[0, 1]
            
            # Calculate alpha (Jensen's alpha)
            asset_mean_return = np.mean(asset_returns)
            market_mean_return = np.mean(market_returns)
            risk_free_rate = 0.06 / 252  # Daily risk-free rate
            
            alpha = asset_mean_return - (risk_free_rate + beta * (market_mean_return - risk_free_rate))
            
            return {
                'beta': round(beta, 3),
                'correlation': round(correlation, 3),
                'alpha': round(alpha * 252 * 100, 3),  # Annualized alpha in %
                'systematic_risk': round(beta**2 * np.var(market_returns), 6),
                'idiosyncratic_risk': round(np.var(asset_returns) - beta**2 * np.var(market_returns), 6)
            }
            
        except Exception as e:
            logger.error(f"❌ Beta calculation error: {e}")
            return {'beta': 1.0, 'correlation': 0, 'alpha': 0}
    
    def optimize_position_size(self, account_balance, risk_tolerance=0.02, confidence_level=0.95):
        """Optimize position size using Kelly Criterion and VaR"""
        try:
            if len(self.price_history) < 20:
                return {'position_size': 0, 'risk_amount': 0, 'method': 'insufficient_data'}
            
            prices = [p['price'] for p in self.price_history]
            returns = np.diff(prices) / prices[:-1]
            
            # Kelly Criterion calculation
            win_rate = len(returns[returns > 0]) / len(returns)
            avg_win = np.mean(returns[returns > 0]) if len(returns[returns > 0]) > 0 else 0
            avg_loss = abs(np.mean(returns[returns < 0])) if len(returns[returns < 0]) > 0 else 0.01
            
            if avg_loss > 0:
                kelly_fraction = win_rate - ((1 - win_rate) / (avg_win / avg_loss))
            else:
                kelly_fraction = 0
            
            # Cap Kelly fraction to prevent over-leveraging
            kelly_fraction = max(0, min(kelly_fraction, 0.25))
            
            # VaR-based position sizing
            var_result = self.calculate_var(confidence_level)
            daily_var = abs(var_result.get('historical_var', 2)) / 100
            
            # Maximum position size based on VaR
            max_var_position = risk_tolerance / daily_var if daily_var > 0 else 0
            
            # Conservative position sizing (minimum of Kelly and VaR methods)
            optimal_fraction = min(kelly_fraction, max_var_position, risk_tolerance * 2)
            
            # Calculate actual position size
            position_value = account_balance * optimal_fraction
            current_price = prices[-1]
            shares = int(position_value / current_price)
            
            # Risk metrics
            position_risk = shares * current_price * daily_var
            
            return {
                'optimal_fraction': round(optimal_fraction, 4),
                'kelly_fraction': round(kelly_fraction, 4),
                'var_fraction': round(max_var_position, 4),
                'shares': shares,
                'position_value': round(shares * current_price, 2),
                'risk_amount': round(position_risk, 2),
                'win_rate': round(win_rate, 3),
                'avg_win': round(avg_win * 100, 3),
                'avg_loss': round(avg_loss * 100, 3),
                'profit_factor': round(avg_win / avg_loss, 3) if avg_loss > 0 else 0,
                'daily_var': round(daily_var * 100, 3)
            }
            
        except Exception as e:
            logger.error(f"❌ Position size optimization error: {e}")
            return {'position_size': 0, 'risk_amount': 0, 'method': 'error'}
    
    def calculate_portfolio_metrics(self, current_price):
        """Calculate comprehensive portfolio metrics"""
        try:
            if not self.portfolio_positions:
                return {'total_value': 0, 'pnl': 0, 'positions': 0}
            
            total_value = 0
            total_pnl = 0
            total_invested = 0
            
            for position in self.portfolio_positions:
                position_value = position['shares'] * current_price
                position_pnl = position_value - position['position_value']
                position_return = position_pnl / position['position_value'] * 100
                
                # Update position metrics
                position['current_value'] = position_value
                position['unrealized_pnl'] = position_pnl
                position['return_pct'] = position_return
                
                # Update peak value and drawdown
                if position_value > position['peak_value']:
                    position['peak_value'] = position_value
                
                drawdown = (position_value - position['peak_value']) / position['peak_value'] * 100
                position['current_drawdown'] = drawdown
                position['max_drawdown'] = min(position.get('max_drawdown', 0), drawdown)
                
                total_value += position_value
                total_pnl += position_pnl
                total_invested += position['position_value']
            
            # Portfolio-level metrics
            portfolio_return = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            
            # Risk metrics
            var_metrics = self.calculate_var()
            sharpe_metrics = self.calculate_sharpe_ratio()
            drawdown_metrics = self.calculate_maximum_drawdown()
            
            return {
                'total_value': round(total_value, 2),
                'total_invested': round(total_invested, 2),
                'total_pnl': round(total_pnl, 2),
                'portfolio_return': round(portfolio_return, 3),
                'num_positions': len(self.portfolio_positions),
                'avg_position_size': round(total_invested / len(self.portfolio_positions), 2),
                'var_1d_95': var_metrics.get('historical_var', 0),
                'expected_shortfall': var_metrics.get('expected_shortfall', 0),
                'sharpe_ratio': sharpe_metrics.get('sharpe_ratio', 0),
                'max_drawdown': drawdown_metrics.get('max_drawdown', 0),
                'current_drawdown': drawdown_metrics.get('current_drawdown', 0),
                'positions': self.portfolio_positions,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Portfolio metrics calculation error: {e}")
            return {'total_value': 0, 'pnl': 0, 'positions': 0, 'error': str(e)}
    
    def generate_risk_alerts(self, current_price, account_balance):
        """Generate risk management alerts"""
        try:
            alerts = []
            
            # Portfolio metrics
            portfolio_metrics = self.calculate_portfolio_metrics(current_price)
            
            # VaR alerts
            var_metrics = self.calculate_var()
            daily_var = abs(var_metrics.get('historical_var', 0))
            
            if daily_var > 3:
                alerts.append({
                    'type': 'HIGH_RISK',
                    'message': f"High VaR detected: {daily_var:.2f}% daily risk",
                    'severity': 'CRITICAL'
                })
            
            # Drawdown alerts
            current_drawdown = portfolio_metrics.get('current_drawdown', 0)
            max_drawdown = portfolio_metrics.get('max_drawdown', 0)
            
            if current_drawdown < -5:
                alerts.append({
                    'type': 'DRAWDOWN',
                    'message': f"Portfolio drawdown: {current_drawdown:.2f}%",
                    'severity': 'HIGH' if current_drawdown < -10 else 'MEDIUM'
                })
            
            # Position size alerts
            total_exposure = portfolio_metrics.get('total_value', 0)
            exposure_ratio = total_exposure / account_balance if account_balance > 0 else 0
            
            if exposure_ratio > 0.8:
                alerts.append({
                    'type': 'OVEREXPOSURE',
                    'message': f"High portfolio exposure: {exposure_ratio:.1%} of account",
                    'severity': 'HIGH'
                })
            
            # Volatility alerts
            volatility = var_metrics.get('volatility', 0)
            if volatility > 25:
                alerts.append({
                    'type': 'HIGH_VOLATILITY',
                    'message': f"High volatility detected: {volatility:.1f}% annualized",
                    'severity': 'MEDIUM'
                })
            
            # Individual position alerts
            for i, position in enumerate(portfolio_metrics.get('positions', [])):
                position_drawdown = position.get('current_drawdown', 0)
                
                if position_drawdown < -8:
                    alerts.append({
                        'type': 'POSITION_LOSS',
                        'message': f"Position {i+1} ({position['symbol']}) down {position_drawdown:.1f}%",
                        'severity': 'HIGH' if position_drawdown < -15 else 'MEDIUM'
                    })
                
                # Stop loss alerts
                if position.get('stop_loss') and current_price <= position['stop_loss']:
                    alerts.append({
                        'type': 'STOP_LOSS',
                        'message': f"Stop loss triggered for {position['symbol']} at ₹{position['stop_loss']}",
                        'severity': 'CRITICAL'
                    })
            
            return {
                'alerts': alerts,
                'num_alerts': len(alerts),
                'risk_level': self._assess_overall_risk_level(alerts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Risk alerts generation error: {e}")
            return {'alerts': [], 'num_alerts': 0, 'risk_level': 'UNKNOWN'}
    
    def _assess_overall_risk_level(self, alerts):
        """Assess overall portfolio risk level"""
        if not alerts:
            return 'LOW'
        
        critical_alerts = len([a for a in alerts if a['severity'] == 'CRITICAL'])
        high_alerts = len([a for a in alerts if a['severity'] == 'HIGH'])
        
        if critical_alerts > 0:
            return 'CRITICAL'
        elif high_alerts > 2:
            return 'HIGH'
        elif high_alerts > 0:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def suggest_risk_adjustments(self, current_price, account_balance):
        """Suggest risk management adjustments"""
        try:
            suggestions = []
            
            # Get current metrics
            portfolio_metrics = self.calculate_portfolio_metrics(current_price)
            var_metrics = self.calculate_var()
            position_opt = self.optimize_position_size(account_balance)
            
            # Position sizing suggestions
            current_exposure = portfolio_metrics.get('total_value', 0) / account_balance
            optimal_exposure = position_opt.get('optimal_fraction', 0.02)
            
            if current_exposure > optimal_exposure * 1.5:
                suggestions.append({
                    'type': 'REDUCE_EXPOSURE',
                    'message': f"Consider reducing position size from {current_exposure:.1%} to {optimal_exposure:.1%}",
                    'priority': 'HIGH'
                })
            
            # Diversification suggestions
            if len(self.portfolio_positions) == 1:
                suggestions.append({
                    'type': 'DIVERSIFICATION',
                    'message': "Consider diversifying across multiple positions or timeframes",
                    'priority': 'MEDIUM'
                })
            
            # Stop loss suggestions
            for position in self.portfolio_positions:
                if not position.get('stop_loss'):
                    atr_stop = current_price * 0.98  # 2% stop loss
                    suggestions.append({
                        'type': 'STOP_LOSS',
                        'message': f"Set stop loss for {position['symbol']} at ₹{atr_stop:.2f}",
                        'priority': 'HIGH'
                    })
            
            # Profit taking suggestions
            for position in self.portfolio_positions:
                return_pct = position.get('return_pct', 0)
                if return_pct > 5 and not position.get('take_profit'):
                    target_price = current_price * 1.03  # 3% above current
                    suggestions.append({
                        'type': 'TAKE_PROFIT',
                        'message': f"Consider partial profit taking for {position['symbol']} at ₹{target_price:.2f}",
                        'priority': 'MEDIUM'
                    })
            
            return {
                'suggestions': suggestions,
                'num_suggestions': len(suggestions),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Risk adjustment suggestions error: {e}")
            return {'suggestions': [], 'num_suggestions': 0}

# Global risk management engine
risk_engine = RiskManagementEngine()

def get_risk_engine():
    """Get the global risk management engine"""
    return risk_engine

if __name__ == "__main__":
    # Test the risk management engine
    engine = RiskManagementEngine()
    
    # Add sample price data
    base_price = 25800
    for i in range(50):
        price = base_price + np.random.normal(0, 20)  # Random walk
        engine.add_price_data(price, volume=100000 + np.random.normal(0, 20000))
    
    # Add sample position
    engine.add_position('NIFTY', 100, 25800, stop_loss=25600, take_profit=26000)
    
    # Test calculations
    var_result = engine.calculate_var()
    sharpe_result = engine.calculate_sharpe_ratio()
    portfolio_metrics = engine.calculate_portfolio_metrics(25850)
    risk_alerts = engine.generate_risk_alerts(25850, 1000000)
    
    print("🛡️ Risk Management Engine Test Results:")
    print(f"VaR (95%): {var_result['historical_var']:.3f}%")
    print(f"Sharpe Ratio: {sharpe_result['sharpe_ratio']:.3f}")
    print(f"Portfolio Return: {portfolio_metrics['portfolio_return']:.2f}%")
    print(f"Risk Alerts: {risk_alerts['num_alerts']}")
    print(f"Risk Level: {risk_alerts['risk_level']}")
    print("✅ Risk Management Engine ready for integration!")