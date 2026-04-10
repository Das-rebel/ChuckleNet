#!/usr/bin/env python3
"""
Year-by-Year Trading Analysis Template
For analyzing trading data from Groww and Upstox platforms
"""

import json
from datetime import datetime

def analyze_yearly_breakdown_template():
    """Template for analyzing yearly trading breakdown from multiple platforms"""

    print("📊 YEAR-BY-YEAR TRADING ANALYSIS TEMPLATE")
    print("=" * 60)
    print("Please provide your trading data in the format below")
    print()

    # Template structure for yearly data
    template = {
        "platforms": {
            "groww": {
                "yearly_data": {
                    # Example format - replace with your actual data
                    "2020": {
                        "f&o": {
                            "pnl": 0,  # P&L in rupees
                            "trades": 0,  # Number of trades
                            "win_rate": 0,  # Percentage
                            "max_win": 0,  # Maximum winning trade
                            "max_loss": 0,  # Maximum losing trade
                            "notes": "Notes for this year"
                        },
                        "stocks": {
                            "pnl": 0,
                            "trades": 0,
                            "win_rate": 0,
                            "max_win": 0,
                            "max_loss": 0,
                            "notes": "Notes for this year"
                        }
                    },
                    "2021": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2022": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2023": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2024": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2025": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    }
                }
            },
            "upstox": {
                "yearly_data": {
                    # Same structure as Groww
                    "2020": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2021": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2022": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2023": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2024": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    },
                    "2025": {
                        "f&o": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0},
                        "stocks": {"pnl": 0, "trades": 0, "win_rate": 0, "max_win": 0, "max_loss": 0}
                    }
                }
            }
        }
    }

    print("📋 DATA INPUT FORMAT:")
    print("=" * 30)
    print("Please provide your trading data in this format:")
    print()

    print("GROWW DATA:")
    print("Year | F&O P&L | F&O Trades | F&O Win% | F&O Max Win | F&O Max Loss | Stock P&L | Stock Trades | Stock Win% | Stock Max Win | Stock Max Loss")
    print("-----|---------|------------|----------|-------------|--------------|----------|--------------|-----------|---------------|---------------")
    print("2020 |         |            |          |             |              |          |              |           |               |              ")
    print("2021 |         |            |          |             |              |          |              |           |               |              ")
    print("2022 |         |            |          |             |              |          |              |           |               |              ")
    print("2023 |         |            |          |             |              |          |              |           |               |              ")
    print("2024 |         |            |          |             |              |          |              |           |               |              ")
    print("2025 |         |            |          |             |              |          |              |           |               |              ")
    print()

    print("UPSTOX DATA:")
    print("(Same format as above)")
    print()

    print("📧 HOW TO PROVIDE DATA:")
    print("=" * 30)
    print("Option 1: Copy-paste the table format above with your actual numbers")
    print("Option 2: Provide data year by year in text format")
    print("Option 3: Share key metrics for each year separately")
    print()

    print("💡 EXAMPLE INPUT:")
    print("GROWW 2020:")
    print("  F&O: P&L: -50000, Trades: 100, Win Rate: 40%, Max Win: 25000, Max Loss: -15000")
    print("  Stocks: P&L: 120000, Trades: 20, Win Rate: 70%, Max Win: 30000, Max Loss: -8000")
    print()

    return template

def analyze_provided_yearly_data():
    """Analyze yearly data once provided"""

    print("\n📈 YEARLY TREND ANALYSIS")
    print("=" * 40)

    # This function will be used once you provide the actual data
    print("Once you provide your yearly data, I will analyze:")
    print("1. Year-over-year performance trends")
    print("2. Platform comparison (Groww vs Upstox)")
    print("3. F&O vs Stock performance by year")
    print("4. Market correlation by year")
    print("5. Capital efficiency by year")
    print("6. Opportunity cost by year")
    print("7. Improvement recommendations by year")

def create_yearly_analysis_function():
    """Create a function to analyze your actual yearly data"""

    analysis_function = '''
def analyze_actual_yearly_data(yearly_data):
    """Analyze your actual yearly trading data"""

    print("📊 ANALYZING YOUR YEARLY TRADING DATA")
    print("=" * 50)

    # Calculate yearly totals and trends
    yearly_summary = {}

    for year, data in yearly_data.items():
        yearly_summary[year] = {
            'total_pnl': data.get('f&p_pnl', 0) + data.get('stocks_pnl', 0),
            'total_trades': data.get('f&o_trades', 0) + data.get('stocks_trades', 0),
            'f&p_performance': data.get('f&p_pnl', 0),
            'stock_performance': data.get('stocks_pnl', 0),
            'best_year': False,
            'worst_year': False
        }

    # Find best and worst years
    performances = {year: summary['total_pnl'] for year, summary in yearly_summary.items()}
    if performances:
        best_year = max(performances, key=performances.get)
        worst_year = min(performances, key=performances.get)

        yearly_summary[best_year]['best_year'] = True
        yearly_summary[worst_year]['worst_year'] = True

    return yearly_summary
'''

    return analysis_function

if __name__ == "__main__":
    template = analyze_yearly_breakdown_template()
    analyze_provided_yearly_data()

    print("\n📄 READY TO ANALYZE YOUR DATA")
    print("=" * 30)
    print("Please provide your yearly trading data and I'll create a comprehensive analysis including:")
    print("- Platform-by-platform performance")
    print("- Year-over-year trends")
    print("- F&O vs Stock breakdown")
    print("- Market comparison for each year")
    print("- Capital efficiency analysis")
    print("- Opportunity cost calculation")
    print("- Improvement recommendations")

    # Save template for reference
    with open('/Users/Subho/yearly_trading_template.json', 'w') as f:
        json.dump(template, f, indent=2)

    print(f"\n📄 Template saved: yearly_trading_template.json")