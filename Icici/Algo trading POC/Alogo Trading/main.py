"""
Main application entry point for the algorithmic trading platform.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from src.core.engine import TradingEngine
from src.core.config import Config
from src.utils.logger import setup_logging


@click.group()
@click.option('--config', '-c', type=str, help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(config: Optional[str], verbose: bool):
    """Algorithmic Trading Platform CLI"""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=log_level)
    
    # Load configuration
    config_path = Path(config) if config else Path('config/default.yaml')
    Config.load(config_path)


@cli.command()
@click.option('--strategy', '-s', required=True, help='Strategy name to run')
@click.option('--paper', is_flag=True, help='Run in paper trading mode')
@click.option('--config-file', '-c', help='Path to configuration file')
def live_trade(strategy: str, paper: bool, config_file: str):
    """Start live trading with specified strategy"""
    click.echo(f"Starting live trading with strategy: {strategy}")
    click.echo(f"Paper trading mode: {'ON' if paper else 'OFF'}")
    
    # Load configuration
    if config_file:
        Config.load(Path(config_file))
    else:
        # Try default ICICI config first
        icici_config = Path('config/icici_breeze.yaml')
        if icici_config.exists():
            Config.load(icici_config)
            click.echo("Using ICICI Breeze configuration")
        else:
            Config.load(Path('config/default.yaml'))
    
    async def run_trading():
        engine = TradingEngine()
        await engine.start(strategy_name=strategy, paper_trading=paper)
    
    asyncio.run(run_trading())


@cli.command()
@click.option('--strategy', '-s', required=True, help='Strategy name to backtest')
@click.option('--start-date', type=str, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=str, help='End date (YYYY-MM-DD)')
@click.option('--initial-capital', type=float, default=100000, help='Initial capital')
def backtest(strategy: str, start_date: str, end_date: str, initial_capital: float):
    """Run backtest for specified strategy"""
    click.echo(f"Running backtest for strategy: {strategy}")
    click.echo(f"Period: {start_date} to {end_date}")
    click.echo(f"Initial capital: ${initial_capital:,.2f}")
    
    from backtesting.backtest_engine import BacktestEngine
    
    engine = BacktestEngine()
    results = engine.run(
        strategy_name=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )
    
    click.echo("\nBacktest Results:")
    click.echo(f"Total Return: {results['total_return']:.2%}")
    click.echo(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    click.echo(f"Max Drawdown: {results['max_drawdown']:.2%}")


@cli.command()
def data_collect():
    """Start data collection process"""
    click.echo("Starting data collection...")
    
    from data.data_collector import DataCollector
    
    collector = DataCollector()
    collector.start()


@cli.command()
def portfolio_status():
    """Display current portfolio status"""
    click.echo("Portfolio Status:")
    
    from portfolio.portfolio_manager import PortfolioManager
    
    portfolio = PortfolioManager()
    status = portfolio.get_status()
    
    click.echo(f"Total Value: ${status['total_value']:,.2f}")
    click.echo(f"Cash: ${status['cash']:,.2f}")
    click.echo(f"Positions: {len(status['positions'])}")


if __name__ == '__main__':
    cli()