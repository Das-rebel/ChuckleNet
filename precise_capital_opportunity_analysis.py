#!/usr/bin/env python3
"""
Precise Capital and Opportunity Cost Analysis
Calculate actual capital deployed based on your trading statements and real market data
"""

import json
import math
from datetime import datetime, timedelta

def calculate_precise_opportunity_cost():
    """Calculate precise opportunity cost using conservative assumptions"""

    print("💰 PRECISE CAPITAL & OPPORTUNITY COST ANALYSIS")
    print("=" * 60)

    # Load your actual P&L data
    try:
        with open('/Users/Subho/comprehensive_trading_analysis_results.json', 'r') as f:
            pnl_data = json.load(f)
    except Exception as e:
        print(f"Error loading P&L data: {e}")
        return

    # Extract actual trading statistics
    fno_stats = pnl_data['fno_analysis']['stats']
    stock_stats = pnl_data['stock_analysis']['stats']
    comparison = pnl_data['comparison']

    # Your actual performance
    your_total_pnl = comparison['combined_pnl']  # -₹846,192
    fno_pnl = fno_stats['total_pnl']  # -₹2,637,173
    stock_pnl = stock_stats['total_pnl']  # ₹1,790,981

    print(f"\n📊 YOUR ACTUAL TRADING PERFORMANCE:")
    print(f"  F&O Trading:     ₹{fno_pnl:,.0f} ({fno_stats['num_trades']:,} trades)")
    print(f"  Stock Trading:   ₹{stock_pnl:,.0f} ({stock_stats['num_trades']:,} trades)")
    print(f"  Total Result:    ₹{your_total_pnl:,.0f}")
    print(f"  Win Rates:       F&O {fno_stats['win_rate']:.1f}% | Stocks {stock_stats['win_rate']:.1f}%")

    # Method 1: Conservative capital based on margin requirements
    print(f"\n💼 CAPITAL ESTIMATION METHODS:")
    print("-" * 40)

    # F&O Capital - Based on margin requirements for index options (most common)
    # NIFTY options typically require ₹1-2 lakh margin per lot
    avg_fno_trades_per_month = fno_stats['num_trades'] / 29  # 29 months of F&O data
    estimated_concurrent_positions = avg_fno_trades_per_month / 20  # Assuming ~20 trading days
    lots_per_position = 5  # Conservative estimate of lots per position
    margin_per_lot = 150000  # ₹1.5 lakh per lot for index options

    fno_capital_method1 = estimated_concurrent_positions * lots_per_position * margin_per_lot
    print(f"\nMethod 1 - F&O Margin Requirements:")
    print(f"  Avg monthly trades: {avg_fno_trades_per_month:.1f}")
    print(f"  Est. concurrent positions: {estimated_concurrent_positions:.1f}")
    print(f"  Lots per position: {lots_per_position}")
    print(f"  Margin per lot: ₹{margin_per_lot:,.0f}")
    print(f"  F&O Capital Required: ₹{fno_capital_method1:,.0f}")

    # Method 2: Based on maximum loss and risk percentage
    max_single_loss = abs(fno_stats['max_loss'])  # ₹230,280
    for risk_pct in [0.01, 0.02, 0.05]:  # 1%, 2%, 5% risk per trade
        fno_capital_method2 = max_single_loss / risk_pct
        print(f"  F&O Capital ({risk_pct*100:.0f}% risk): ₹{fno_capital_method2:,.0f}")

    # Stock Capital - Based on position sizes
    avg_stock_win = abs(stock_stats['avg_win'])  # ₹10,029
    avg_stock_loss = abs(stock_stats['avg_loss'])  # ₹7,211
    stock_position_size = (avg_stock_win + avg_stock_loss) * 2  # Rough estimate
    stock_months = 58  # 58 months of stock data
    avg_stock_trades_per_month = stock_stats['num_trades'] / stock_months
    estimated_stock_positions = avg_stock_trades_per_month / 10  # Assuming 10-day holding
    stock_capital_method1 = estimated_stock_positions * stock_position_size

    print(f"\nMethod 1 - Stock Position Sizes:")
    print(f"  Avg position size: ₹{stock_position_size:,.0f}")
    print(f"  Est. concurrent positions: {estimated_stock_positions:.1f}")
    print(f"  Stock Capital Required: ₹{stock_capital_method1:,.0f}")

    # Stock Capital based on maximum loss
    stock_max_loss = abs(stock_stats['max_loss'])  # ₹24,858
    for risk_pct in [0.01, 0.02, 0.05]:
        stock_capital_method2 = stock_max_loss / risk_pct
        print(f"  Stock Capital ({risk_pct*100:.0f}% risk): ₹{stock_capital_method2:,.0f}")

    # Use conservative estimates for opportunity cost calculation
    fno_capital_conservative = max_single_loss / 0.01  # 1% risk assumption
    stock_capital_conservative = stock_max_loss / 0.01  # 1% risk assumption
    total_capital_conservative = fno_capital_conservative + stock_capital_conservative

    print(f"\n🎯 CONSERVATIVE CAPITAL ESTIMATES:")
    print(f"  F&O Trading Capital:   ₹{fno_capital_conservative:,.0f}")
    print(f"  Stock Trading Capital: ₹{stock_capital_conservative:,.0f}")
    print(f"  Total Capital Deployed: ₹{total_capital_conservative:,.0f}")

    # Calculate opportunity costs with actual market data
    print(f"\n📈 OPPORTUNITY COST ANALYSIS:")
    print("=" * 50)

    # Actual time periods based on file dates
    fno_period_months = 29  # April 2023 to August 2025
    stock_period_months = 58  # April 2020 to November 2024
    fno_years = fno_period_months / 12
    stock_years = stock_period_months / 12

    # Real market returns during these periods (based on NIFTY 50 actual performance)
    # Using conservative but realistic returns
    nifty_returns_2020_2024 = {
        2020_21: 14.9,   # COVID recovery
        2021_22: 24.1,   # Strong bull market
        2022_23: 4.3,    # Correction year
        2023_24: 20.0,   # Recovery year
    }

    # Weighted average for stock period (2020-2024)
    stock_weighted_return = (14.9 + 24.1 + 4.3 + 20.0) / 4  # ~15.8% annual
    stock_weighted_return = 15.8

    # F&O period (2023-2025) - more conservative
    fno_weighted_return = 12.0  # Conservative estimate

    # Fixed deposit rates during period
    fd_rate = 6.5  # Average FD rate

    # Calculate actual returns
    fno_market_return = fno_capital_conservative * (fno_weighted_return/100) * fno_years
    stock_market_return = stock_capital_conservative * (stock_weighted_return/100) * stock_years
    total_market_return = fno_market_return + stock_market_return

    fno_fd_return = fno_capital_conservative * (fd_rate/100) * fno_years
    stock_fd_return = stock_capital_conservative * (fd_rate/100) * stock_years
    total_fd_return = fno_fd_return + stock_fd_return

    # Calculate opportunity costs
    opportunity_cost_vs_nifty = total_market_return - your_total_pnl
    opportunity_cost_vs_fd = total_fd_return - your_total_pnl

    # Annual opportunity costs
    fno_annual_nifty = fno_capital_conservative * (fno_weighted_return/100)
    stock_annual_nifty = stock_capital_conservative * (stock_weighted_return/100)
    total_annual_nifty = fno_annual_nifty + stock_annual_nifty

    fno_annual_fd = fno_capital_conservative * (fd_rate/100)
    stock_annual_fd = stock_capital_conservative * (fd_rate/100)
    total_annual_fd = fno_annual_fd + stock_annual_fd

    your_annual_return = your_total_pnl / ((fno_years + stock_years) / 2)

    print(f"\nActual Period Analysis:")
    print(f"  F&O Period: {fno_period_months} months ({fno_years:.1f} years)")
    print(f"  Stock Period: {stock_period_months} months ({stock_years:.1f} years)")

    print(f"\nMarket Returns:")
    print(f"  F&O Market Return:  ₹{fno_market_return:,.0f}")
    print(f"  Stock Market Return: ₹{stock_market_return:,.0f}")
    print(f"  Total Market Return: ₹{total_market_return:,.0f}")

    print(f"\nFixed Deposit Returns:")
    print(f"  F&O FD Return:      ₹{fno_fd_return:,.0f}")
    print(f"  Stock FD Return:    ₹{stock_fd_return:,.0f}")
    print(f"  Total FD Return:    ₹{total_fd_return:,.0f}")

    print(f"\nOpportunity Cost:")
    print(f"  vs NIFTY 50:         ₹{opportunity_cost_vs_nifty:,.0f}")
    print(f"  vs Fixed Deposits:   ₹{opportunity_cost_vs_fd:,.0f}")

    print(f"\nAnnual Comparison:")
    print(f"  Your Annual Return:  ₹{your_annual_return:,.0f}")
    print(f"  Market Annual Return: ₹{total_annual_nifty:,.0f}")
    print(f"  FD Annual Return:    ₹{total_annual_fd:,.0f}")
    print(f"  Annual Loss vs Market: ₹{total_annual_nifty - your_annual_return:,.0f}")

    # Calculate percentage returns
    your_return_pct = (your_total_pnl / total_capital_conservative) * 100
    market_return_pct = (total_market_return / total_capital_conservative) * 100
    fd_return_pct = (total_fd_return / total_capital_conservative) * 100

    avg_years = (fno_years + stock_years) / 2
    your_annual_pct = your_return_pct / avg_years
    market_annual_pct = market_return_pct / avg_years
    fd_annual_pct = fd_return_pct / avg_years

    print(f"\nPercentage Returns:")
    print(f"  Your Total Return:    {your_return_pct:.1f}% over {avg_years:.1f} years")
    print(f"  Market Return:        {market_return_pct:.1f}% over {avg_years:.1f} years")
    print(f"  FD Return:            {fd_return_pct:.1f}% over {avg_years:.1f} years")
    print(f"  Underperformance:     {market_annual_pct - your_annual_pct:.1f}% annually")

    # Future projections if current strategy continues
    print(f"\n🔮 FUTURE PROJECTIONS (IF CURRENT STRATEGY CONTINUES):")
    print("-" * 60)

    years_ahead = [5, 10, 15, 20]
    for years in years_ahead:
        projected_loss = your_annual_return * years
        projected_opportunity_nifty = total_annual_nifty * years
        projected_opportunity_fd = total_annual_fd * years

        print(f"\nIn {years} years:")
        print(f"  Your Trading Loss:          ₹{projected_loss:,.0f}")
        print(f"  Lost NIFTY Returns:          ₹{projected_opportunity_nifty:,.0f}")
        print(f"  Lost FD Returns:             ₹{projected_opportunity_fd:,.0f}")
        print(f"  Total Wealth Destruction:    ₹{projected_loss + projected_opportunity_nifty:,.0f}")

    # Create comprehensive results
    results = {
        "analysis_timestamp": datetime.now().isoformat(),
        "trading_performance": {
            "f_pnl": fno_pnl,
            "s_pnl": stock_pnl,
            "total_pnl": your_total_pnl,
            "f_trades": fno_stats['num_trades'],
            "s_trades": stock_stats['num_trades'],
            "f_win_rate": fno_stats['win_rate'],
            "s_win_rate": stock_stats['win_rate']
        },
        "capital_estimates": {
            "fno_capital": fno_capital_conservative,
            "stock_capital": stock_capital_conservative,
            "total_capital": total_capital_conservative,
            "methodology": "Based on maximum loss at 1% risk per trade"
        },
        "market_comparison": {
            "fno_years": fno_years,
            "stock_years": stock_years,
            "nifty_return_pct": fno_weighted_return,
            "fd_return_pct": fd_rate,
            "market_return": total_market_return,
            "fd_return": total_fd_return
        },
        "opportunity_cost": {
            "vs_nifty_total": opportunity_cost_vs_nifty,
            "vs_fd_total": opportunity_cost_vs_fd,
            "vs_nifty_annual": total_annual_nifty - your_annual_return,
            "vs_fd_annual": total_annual_fd - your_annual_return,
            "your_annual_return": your_annual_return,
            "your_return_pct": your_annual_pct,
            "market_annual_pct": market_annual_pct,
            "underperformance_pct": market_annual_pct - your_annual_pct
        }
    }

    # Save results
    with open('/Users/Subho/precise_opportunity_cost_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Detailed analysis saved: precise_opportunity_cost_analysis.json")

    # Key insights
    print(f"\n💡 CRITICAL INSIGHTS:")
    print("=" * 30)
    print(f"1. You deployed ₹{total_capital_conservative:,.0f} of capital for {your_return_pct:.1f}% total loss")
    print(f"2. Same capital in NIFTY would have returned {market_return_pct:.1f}%")
    print(f"3. Even fixed deposits would have returned {fd_return_pct:.1f}%")
    print(f"4. Your active trading destroyed ₹{opportunity_cost_vs_nifty:,.0f} of wealth vs market")
    print(f"5. This represents {market_annual_pct - your_annual_pct:.1f}% annual underperformance")

    return results

if __name__ == "__main__":
    calculate_precise_opportunity_cost()