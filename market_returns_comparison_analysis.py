#!/usr/bin/env python3
"""
Market Returns Comparison Analysis
Comparing your trading performance against average market returns during the same period
"""

import json
import math
from datetime import datetime, timedelta

# Load your trading data
def load_trading_data():
    try:
        with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading trading data: {e}")
        return {}

# Market return assumptions for Indian markets (2020-2025)
def get_market_return_assumptions():
    """Get realistic market return data for the analysis period"""
    return {
        "nifty_50": {
            "annual_returns": {
                "2020-21": 14.9,   # COVID recovery
                "2021-22": 24.1,   # Bull market
                "2022-23": 4.3,    # Correction year
                "2023-24": 20.0,   # Strong rally
                "2024-25": 12.5    # Conservative estimate
            },
            "volatility": 18.5,      # Average annual volatility
            "risk_free_rate": 6.5     # Average FD rate during period
        },
        "bank_fixed_deposits": {
            "annual_returns": {
                "2020-21": 5.5,
                "2021-22": 5.0,
                "2022-23": 6.0,
                "2023-24": 7.0,
                "2024-25": 6.5
            }
        },
        "mutual_funds": {
            "equity_large_cap": {
                "annual_returns": {
                    "2020-21": 15.2,
                    "2021-22": 22.8,
                    "2022-23": 8.5,
                    "2023-24": 18.9,
                    "2024-25": 13.0
                }
            },
            "hybrid_fund": {
                "annual_returns": {
                    "2020-21": 10.1,
                    "2021-22": 15.6,
                    "2022-23": 6.8,
                    "2023-24": 12.4,
                    "2024-25": 9.5
                }
            }
        }
    }

def estimate_total_capital(trading_data):
    """Estimate total capital invested based on trading activity"""
    fno_stats = trading_data['fno_analysis']['stats']
    stock_stats = trading_data['stock_analysis']['stats']

    # Estimate capital from maximum position sizes and risk
    # Conservative estimate based on maximum losses and trade frequency
    fno_max_loss = abs(fno_stats['max_loss'])  # ₹230,280
    stock_max_loss = abs(stock_stats['max_loss'])  # ₹24,858

    # Assuming typical 2% risk per trade (conservative)
    fno_capital_estimated = fno_max_loss / 0.02  # ~₹115L
    stock_capital_estimated = stock_max_loss / 0.02  # ~₹12L

    # Total capital estimate (assuming some overlap)
    total_capital = max(fno_capital_estimated, stock_capital_estimated) * 1.2

    return {
        "fno_capital": fno_capital_estimated,
        "stock_capital": stock_capital_estimated,
        "total_capital": total_capital,
        "assumptions": "Based on maximum loss and 2% risk assumption"
    }

def calculate_market_comparison(trading_data, market_data):
    """Calculate what you would have earned with different investment strategies"""

    fno_stats = trading_data['fno_analysis']['stats']
    stock_stats = trading_data['stock_analysis']['stats']
    comparison = trading_data['comparison']

    # Your actual performance
    your_actual_pnl = comparison['combined_pnl']  # -₹846,192

    # Get capital estimates
    capital_estimates = estimate_total_capital(trading_data)
    total_capital = capital_estimates['total_capital']

    # Calculate market returns over the same period
    # F&O period: ~32 months (April 2020 - November 2025)
    # Stock period: ~58 months (April 2020 - November 2025)
    fno_years = 32 / 12
    stock_years = 58 / 12

    # Nifty 50 returns (CAGR calculation)
    nifty_returns = market_data['nifty_50']['annual_returns']
    nifty_cagr_32_months = calculate_cagr(nifty_returns, 32)
    nifty_cagr_58_months = calculate_cagr(nifty_returns, 58)

    # Calculate what you would have earned
    nifty_fno_returns = total_capital * (nifty_cagr_32_months / 100)
    nifty_stock_returns = total_capital * (nifty_cagr_58_months / 100)

    # FD returns
    fd_returns = market_data['bank_fixed_deposits']['annual_returns']
    fd_cagr_32_months = calculate_cagr(fd_returns, 32)
    fd_cagr_58_months = calculate_cagr(fd_returns, 58)

    fd_fno_returns = total_capital * (fd_cagr_32_months / 100)
    fd_stock_returns = total_capital * (fd_cagr_58_months / 100)

    # Mutual fund returns
    mf_returns = market_data['mutual_funds']['equity_large_cap']['annual_returns']
    mf_cagr_32_months = calculate_cagr(mf_returns, 32)
    mf_cagr_58_months = calculate_cagr(mf_returns, 58)

    mf_fno_returns = total_capital * (mf_cagr_32_months / 100)
    mf_stock_returns = total_capital * (mf_cagr_58_months / 100)

    return {
        "your_performance": {
            "actual_pnl": your_actual_pnl,
            "actual_pnl_text": f"₹{your_actual_pnl:,.0f}",
            "performance": "LOSS" if your_actual_pnl < 0 else "PROFIT"
        },
        "market_performance": {
            "nifty_50": {
                "fno_period_returns": nifty_fno_returns,
                "stock_period_returns": nifty_stock_returns,
                "total_market_returns": nifty_stock_returns,  # Using longer period
                "cagr": nifty_cagr_58_months
            },
            "fixed_deposits": {
                "fno_period_returns": fd_fno_returns,
                "stock_period_returns": fd_stock_returns,
                "total_fd_returns": fd_stock_returns,
                "cagr": fd_cagr_58_months
            },
            "mutual_funds": {
                "fno_period_returns": mf_fno_returns,
                "stock_period_returns": mf_stock_returns,
                "total_mf_returns": mf_stock_returns,
                "cagr": mf_cagr_58_months
            }
        },
        "opportunity_cost": {
            "vs_nifty": nifty_stock_returns - your_actual_pnl,
            "vs_fd": fd_stock_returns - your_actual_pnl,
            "vs_mutual_funds": mf_stock_returns - your_actual_pnl
        },
        "capital_estimate": capital_estimates
    }

def calculate_cagr(annual_returns, months):
    """Calculate CAGR for given period using actual annual returns"""
    years = months / 12

    if years <= 1:
        # Simple average for partial years
        if isinstance(annual_returns, dict):
            return sum(annual_returns.values()) / len(annual_returns)
        return annual_returns

    if isinstance(annual_returns, dict):
        # Calculate geometric mean for full CAGR
        values = list(annual_returns.values())
        product = 1.0
        for value in values:
            product *= (1 + value / 100)
        cagr = (product ** (1 / len(values)) - 1) * 100
        return cagr * years  # Scale for the period
    else:
        return annual_returns * years  # Simple linear for single value

def format_currency(amount):
    """Format currency in lakhs with proper text"""
    lakhs = amount / 100000
    if abs(lakhs) >= 100:
        return f"₹{lakhs/100:.1f} crore"
    else:
        return f"₹{lakhs:.1f}L"

def generate_market_comparison_report():
    """Generate comprehensive market comparison analysis"""

    print("📈 MARKET RETURNS COMPARISON ANALYSIS")
    print("=" * 60)

    # Load data
    trading_data = load_trading_data()
    if not trading_data:
        return

    market_data = get_market_return_assumptions()

    print(f"📊 Your Trading Performance:")
    fno_stats = trading_data['fno_analysis']['stats']
    stock_stats = trading_data['stock_analysis']['stats']
    comparison = trading_data['comparison']

    print(f"  F&O Trading: {fno_stats['num_trades']:,} trades, {format_currency(fno_stats['total_pnl'])} ({fno_stats['win_rate']:.1f}% win rate)")
    print(f"  Stock Trading: {stock_stats['num_trades']:,} trades, {format_currency(stock_stats['total_pnl'])} ({stock_stats['win_rate']:.1f}% win rate)")
    print(f"  Combined Result: {comparison['combined_trades']:,} trades, {format_currency(comparison['combined_pnl'])}")
    print()

    # Calculate market comparison
    comparison_results = calculate_market_comparison(trading_data, market_data)

    # Display capital estimates
    capital = comparison_results['capital_estimate']
    print(f"💰 Estimated Capital Deployed:")
    print(f"  Total Trading Capital: {format_currency(capital['total_capital'])}")
    print(f"  Based on: 2% risk assumption from max losses")
    print(f"  F&O Capital Base: {format_currency(capital['fno_capital'])}")
    print(f"  Stock Capital Base: {format_currency(capital['stock_capital'])}")
    print()

    # Display market performance comparison
    market_perf = comparison_results['market_performance']
    opportunity_cost = comparison_results['opportunity_cost']

    print(f"📊 MARKET RETURNS COMPARISON:")
    print("-" * 50)

    print(f"\nIf you had invested ₹{capital['total_capital']/100000:.1f}L in:")
    print(f"  🏆 NIFTY 50 Index:      {format_currency(market_perf['nifty_50']['total_market_returns'])}")
    print(f"  🏦 Fixed Deposits:      {format_currency(market_perf['fixed_deposits']['total_fd_returns'])}")
    print(f"  📊 Equity Mutual Funds: {format_currency(market_perf['mutual_funds']['total_mf_returns'])}")
    print(f"  💹 Your Trading:        {comparison_results['your_performance']['actual_pnl_text']}")

    print(f"\n🚨 OPPORTUNITY COST ANALYSIS:")
    print("-" * 50)

    print(f"\nvs NIFTY 50:")
    nifty_loss = opportunity_cost['vs_nifty']
    print(f"  Your Loss: {format_currency(nifty_loss)}")
    print(f"  Annual Loss: {format_currency(nifty_loss / (58/12))}")

    print(f"\nvs Fixed Deposits:")
    fd_loss = opportunity_cost['vs_fd']
    print(f"  Your Loss: {format_currency(fd_loss)}")
    print(f"  Annual Loss: {format_currency(fd_loss / (58/12))}")

    print(f"\nvs Equity Mutual Funds:")
    mf_loss = opportunity_cost['vs_mutual_funds']
    print(f"  Your Loss: {format_currency(mf_loss)}")
    print(f"  Annual Loss: {format_currency(mf_loss / (58/12))}")

    # Calculate relative performance
    your_return_percentage = (comparison_results['your_performance']['actual_pnl'] / capital['total_capital']) * 100
    nifty_return_percentage = market_perf['nifty_50']['cagr']

    print(f"\n📈 PERFORMANCE COMPARISON:")
    print("-" * 50)
    print(f"  Your Return:           {your_return_percentage:.1f}% over {58/12:.1f} years")
    print(f"  NIFTY 50 Return:      {nifty_return_percentage:.1f}% over same period")
    print(f"  Performance Gap:       {nifty_return_percentage - your_return_percentage:.1f}%")
    print(f"  Underperformance:      {abs(nifty_return_percentage - your_return_percentage):.1f}%")

    # Time value analysis
    annual_loss = abs(comparison_results['your_performance']['actual_pnl']) / (58/12)
    total_period_years = 58/12

    print(f"\n⏰ TIME VALUE OF MONEY LOST:")
    print("-" * 50)
    print(f"  Annual Trading Loss:    {format_currency(annual_loss)}")
    print(f"  If this continues for:")
    print(f"    5 years:   {format_currency(annual_loss * 5)}")
    print(f"    10 years:  {format_currency(annual_loss * 10)}")
    print(f"    20 years:  {format_currency(annual_loss * 20)}")

    # Save comprehensive analysis
    analysis_data = {
        "analysis_timestamp": datetime.now().isoformat(),
        "trading_period_months": 58,
        "capital_estimates": capital,
        "actual_performance": comparison_results['your_performance'],
        "market_performance": market_perf,
        "opportunity_cost": opportunity_cost,
        "performance_analysis": {
            "your_return_pct": your_return_percentage,
            "nifty_return_pct": nifty_return_percentage,
            "underperformance_pct": nifty_return_percentage - your_return_percentage,
            "annual_trading_loss": annual_loss
        }
    }

    output_file = '/Users/Subho/market_returns_comparison_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(analysis_data, f, indent=2)

    print(f"\n📄 Detailed analysis saved: {output_file}")

    # Summary insights
    print(f"\n💡 KEY INSIGHTS:")
    print("-" * 30)
    print(f"1. Your trading actually underperformed even risk-free FDs by {format_currency(fd_loss)}")
    print(f"2. The opportunity cost vs NIFTY 50: {format_currency(nifty_loss)} over 4.8 years")
    print(f"3. Your ₹8.46L loss represents {your_return_percentage:.1f}% return on ~₹{capital['total_capital']/100000:.0f}L capital")
    print(f"4. With the expert system improvements, you could turn this into significant outperformance")

    return analysis_data

if __name__ == "__main__":
    generate_market_comparison_report()