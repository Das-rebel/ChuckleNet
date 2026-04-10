#!/usr/bin/env python3
"""
SPECIALIZED OPTIONS TRADING EXTRACTOR
Fine-tuned for Indian Options Trading signals from your actual group
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from collections import Counter
import re

try:
    from PIL import ImageGrab
    import pytesseract
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptionsTradingExtractor:
    """Specialized extractor for Indian Options Trading signals"""

    def __init__(self):
        self.target_group = -2127259353
        self.bot_username = "@Das_ts_bot"
        self.results_dir = "options_trading_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

        # Indian stock symbols (NSE, BSE)
        self.stock_symbols = {
            'RELIANCE', 'TCS', 'HDFC', 'INFY', 'HDFCBANK', 'ICICIBANK', 'KOTAKBANK',
            'HINDUNILVR', 'SBIN', 'BAJFINANCE', 'MARUTI', 'LT', 'WIPRO', 'AXISBANK',
            'ASIANPAINT', 'DMART', 'NESTLEIND', 'GRASIM', 'HCLTECH', 'ULTRACEMCO',
            'TECHM', 'TITAN', 'SUNPHARMA', 'M&M', 'POWERGRID', 'NTPC', 'BPCL',
            'COALINDIA', 'ONGC', 'GAIL', 'IOC', 'BHARTIARTL', 'JSWSTEEL',
            'TATASTEEL', 'VEDL', 'DRREDDY', 'CIPLA', 'AUROPHARMA', 'VOLTAS',
            'PGEL', 'INDUSTOWER', 'SASL', 'BEECH', 'DABUR', 'DIVISLAB'
        }

        # Options trading actions and patterns
        self.options_actions = {
            'BUY', 'SELL', 'CE', 'PE', 'CALL', 'PUT', 'EXIT', 'ENTRY',
            'CTC', 'COST', 'BETTER', 'TARGET', 'STOPLOSS', 'SL', 'TP',
            'BOOK', 'PROFIT', 'LOSS', 'HOLD', 'ADD', 'SQUARE', 'OFF'
        }

        # Options expiry patterns
        self.expiry_patterns = [
            r'\d{1,2}[A-Z]{3}\d{2}',  # 15NOV23 format
            r'[A-Z]{3}\d{2}',         # NOV23 format
            r'WEEKLY', 'MONTHLY', 'W1', 'W2', 'W3', 'W4'
        ]

        # Strike price patterns
        self.strike_patterns = [
            r'\b\d{3,5}\s*CE\b',    # 1220 CE
            r'\b\d{3,5}\s*PE\b',    # 1360 PE
            r'\bCE\s*\d{3,5}\b',    # CE 1220
            r'\bPE\s*\d{3,5}\b',    # PE 1360
        ]

    def extract_options_signals(self, text):
        """Extract Options trading signals from text"""
        if not text or len(text.strip()) < 10:
            return []

        text_upper = text.upper()
        signals = []

        # Look for options trading patterns
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            if len(line) < 5:
                continue

            # Check for options keywords
            if any(keyword in line.upper() for keyword in ['CE', 'PE', 'CALL', 'PUT', 'OPTION']):
                signal = self.analyze_options_line(line, line_num)
                if signal:
                    signals.append(signal)

        return signals

    def analyze_options_line(self, line, line_num):
        """Analyze a single line for options trading signals"""
        line_upper = line.upper()

        # Extract stock symbol
        stock_symbol = None
        for symbol in self.stock_symbols:
            if symbol in line_upper:
                stock_symbol = symbol
                break

        # Extract strike price and option type
        strikes = []
        option_types = []

        # Pattern: SYMBOL PRICE CE/PE - ACTION
        strike_ce = re.findall(r'(\d{3,5})\s*CE', line_upper)
        strike_pe = re.findall(r'(\d{3,5})\s*PE', line_upper)

        for strike in strike_ce:
            strikes.append(strike)
            option_types.append('CE')

        for strike in strike_pe:
            strikes.append(strike)
            option_types.append('PE')

        # Extract actions
        actions = []
        for action in self.options_actions:
            if action in line_upper:
                actions.append(action)

        # Extract profit/loss targets
        profit_targets = re.findall(r'(?:PROFIT|GAIN|TARGET)\s*[:\-]?\s*[\d,]+', line_upper)
        loss_targets = re.findall(r'(?:LOSS|SL|STOP)\s*[:\-]?\s*[\d,]+', line_upper)

        # Calculate confidence
        confidence = 0.0
        if stock_symbol:
            confidence += 0.3
        if strikes:
            confidence += 0.3
        if actions:
            confidence += 0.2
        if profit_targets or loss_targets:
            confidence += 0.2

        if confidence > 0.4:
            signal = {
                "line_number": line_num,
                "original_text": line,
                "stock_symbol": stock_symbol or "UNKNOWN",
                "strike_prices": strikes,
                "option_types": option_types,
                "actions": actions,
                "profit_targets": profit_targets,
                "loss_targets": loss_targets,
                "confidence_score": min(confidence, 1.0),
                "signal_type": "options_trading",
                "extracted_date": datetime.now().isoformat()
            }

            # Generate summary
            summary_parts = []
            if stock_symbol:
                summary_parts.append(stock_symbol)
            for strike, opt_type in zip(strikes[:2], option_types[:2]):
                summary_parts.append(f"{strike} {opt_type}")
            if actions:
                summary_parts.append(actions[0])

            signal["summary"] = " ".join(summary_parts)
            return signal

        return None

    def analyze_captured_content(self):
        """Analyze the actual options trading content we captured"""
        print("🎯 OPTIONS TRADING CONTENT ANALYSIS")
        print("=" * 50)

        # Read the captured content files
        content_files = []
        for file in os.listdir("refined_trading_analysis"):
            if file.startswith("trading_content_") and file.endswith(".txt"):
                content_files.append(os.path.join("refined_trading_analysis", file))

        print(f"📁 Found {len(content_files)} content files to analyze")

        all_signals = []
        for content_file in content_files:
            print(f"📋 Analyzing: {os.path.basename(content_file)}")

            try:
                with open(content_file, 'r') as f:
                    content = f.read()

                # Extract options signals
                signals = self.extract_options_signals(content)
                all_signals.extend(signals)

                if signals:
                    print(f"   🎯 Found {len(signals)} options signals:")
                    for signal in signals[:3]:  # Show first 3
                        print(f"      • {signal['summary']}")
                else:
                    print("   ⚠️ No options signals found")

            except Exception as e:
                print(f"   ❌ Error analyzing file: {e}")

        if all_signals:
            self.generate_options_analysis_report(all_signals)
        else:
            print("📊 No options trading signals found in captured content")

        return all_signals

    def generate_options_analysis_report(self, signals):
        """Generate comprehensive options trading analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Analyze the signals
        all_stocks = [s.get('stock_symbol', 'UNKNOWN') for s in signals]
        all_options = [opt for s in signals for opt in s.get('option_types', [])]
        all_actions = [act for s in signals for act in s.get('actions', [])]
        all_confidences = [s.get('confidence_score', 0) for s in signals]

        stock_counts = Counter(all_stocks)
        option_counts = Counter(all_options)
        action_counts = Counter(all_actions)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

        # Generate detailed analysis
        detailed_signals = []
        for signal in signals:
            detailed_signal = {
                **signal,
                "risk_assessment": self.assess_options_risk(signal),
                "recommendation": self.generate_options_recommendation(signal)
            }
            detailed_signals.append(detailed_signal)

        # Save JSON report
        json_file = os.path.join(self.results_dir, f"options_analysis_{timestamp}.json")
        report = {
            "options_trading_summary": {
                "total_signals": len(signals),
                "average_confidence": avg_confidence,
                "analysis_date": datetime.now().isoformat(),
                "group_type": "Indian Options Trading",
                "exchange": "NSE/BSE"
            },
            "stock_analysis": dict(stock_counts.most_common()),
            "option_type_analysis": dict(option_counts.most_common()),
            "action_analysis": dict(action_counts.most_common()),
            "signals": detailed_signals
        }

        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate readable report
        readable_file = os.path.join(self.results_dir, f"options_summary_{timestamp}.txt")
        readable_report = f"""
🎯 INDIAN OPTIONS TRADING ANALYSIS REPORT
=========================================

📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
🎯 Target Group: {self.target_group}
📊 Total Signals: {len(signals)}
📈 Average Confidence: {avg_confidence:.1%}
💼 Exchange: NSE/BSE Options

📈 TOP STOCKS TRADED:
--------------------
"""

        if stock_counts:
            for stock, count in stock_counts.most_common(10):
                readable_report += f"   • {stock}: {count} signals\n"

        readable_report += f"""
📊 OPTION TYPES:
---------------
"""

        if option_counts:
            for opt_type, count in option_counts.most_common():
                readable_report += f"   • {opt_type}: {count} contracts\n"

        readable_report += f"""
⚡ TRADING ACTIONS:
------------------
"""

        if action_counts:
            for action, count in action_counts.most_common():
                readable_report += f"   • {action}: {count} instances\n"

        readable_report += f"""
🎯 DETAILED SIGNALS:
--------------------
"""

        for i, signal in enumerate(detailed_signals[:10], 1):  # Show top 10
            readable_report += f"\n{i}. {signal['summary']} (Confidence: {signal['confidence_score']:.1%})\n"
            readable_report += f"   📊 Stock: {signal['stock_symbol']}\n"
            readable_report += f"   💰 Strikes: {', '.join(signal['strike_prices'])}\n"
            readable_report += f"   📋 Types: {', '.join(signal['option_types'])}\n"
            readable_report += f"   ⚡ Actions: {', '.join(signal['actions'])}\n"
            readable_report += f"   ⚠️  Risk: {signal['risk_assessment']}\n"
            readable_report += f"   💡 Recommendation: {signal['recommendation']}\n"

        readable_report += f"""
🎯 TRADING INSIGHTS:
------------------
• Most Active Stock: {stock_counts.most_common(1)[0][0] if stock_counts else 'N/A'}
• Preferred Option Type: {option_counts.most_common(1)[0] if option_counts else 'N/A'}
• Common Action: {action_counts.most_common(1)[0] if action_counts else 'N/A'}

💡 STRATEGY RECOMMENDATIONS:
• Focus on {stock_counts.most_common(1)[0][0] if stock_counts else 'high-volume stocks'}
• Consider {option_counts.most_common(1)[0] if option_counts else 'both CE and PE options'}
• Follow {action_counts.most_common(1)[0] if action_counts else 'entry/exit signals'}

⚠️ RISK DISCLAIMER:
Options trading involves high risk. Please trade with proper
risk management and only with money you can afford to lose.
"""

        with open(readable_file, 'w') as f:
            f.write(readable_report)

        # Display results
        print("\n" + "=" * 60)
        print("🎉 OPTIONS TRADING ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"📊 Options Signals: {len(signals)}")
        print(f"📈 Average Confidence: {avg_confidence:.1%}")
        if stock_counts:
            print(f"📈 Top Stock: {stock_counts.most_common(1)[0][0]}")
        print(f"💾 JSON Report: {json_file}")
        print(f"📋 Summary: {readable_file}")
        print("=" * 60)

    def assess_options_risk(self, signal):
        """Assess risk level for options signal"""
        risk_score = 0

        # High risk indicators
        high_risk_actions = ['BUY', 'FUTURES', 'LEVERAGE']
        for action in high_risk_actions:
            if action in signal.get('actions', []):
                risk_score += 2

        # Medium risk indicators
        if signal.get('stock_symbol') == 'UNKNOWN':
            risk_score += 1

        # Low risk indicators
        if 'EXIT' in signal.get('actions', []):
            risk_score -= 1
        if 'PROFIT' in signal.get('actions', []):
            risk_score -= 1

        if risk_score >= 2:
            return "HIGH"
        elif risk_score >= 1:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_options_recommendation(self, signal):
        """Generate recommendation for options signal"""
        if 'EXIT' in signal.get('actions', []):
            return "Consider booking profits/losses as suggested"
        elif 'BUY' in signal.get('actions', []):
            return "Verify entry points and set stop losses"
        elif 'TARGET' in signal.get('actions', []):
            return "Monitor levels closely for target achievement"
        elif 'PROFIT' in signal.get('actions', []):
            return "Profit booking opportunity identified"
        else:
            return "Monitor signal for further confirmation"

    def create_manual_options_guide(self):
        """Create a guide for manual options signal extraction"""
        guide = """
🎯 INDIAN OPTIONS TRADING - MANUAL GUIDE
=====================================

📋 WHAT TO LOOK FOR IN YOUR GROUP:

1. 📊 STOCK SYMBOLS:
   Look for NSE/BSE stock names:
   • AUROPHARMA, VOLTAS, INDUSTOWER, PGEL
   • RELIANCE, TCS, INFY, HDFCBANK
   • BANKNIFTY, NIFTY indices

2. 💰 OPTION CONTRACTS:
   Pattern: [STOCK] [STRIKE] [TYPE]
   Examples:
   • AUROPHARMA 1220 CE
   • VOLTAS 1360 PE
   • PGEL 570 CE

3. ⚡ TRADING ACTIONS:
   • CE/PE: Call/Put options
   • ENTRY/BUY: Enter position
   • EXIT/SELL: Exit position
   • TARGET: Price target
   • SL/STOP: Stop loss

4. 📈 PROFIT/LOSS:
   • "2100 PROFIT" = ₹2,100 profit
   • "CTC EXIT" = Cost to cost exit
   • "BETTER" = Better levels available

🤖 IMMEDIATE ACTION:
Forward any options trading message to @Das_ts_bot for instant AI analysis!

📊 SAMPLE SIGNALS TO LOOK FOR:
✅ "AUROPHARMA 1220 CE - CTC EXIT"
✅ "VOLTAS 1360 CE - CTC EXIT"
✅ "PGEL 570 CE - 2,100 PROFIT"
✅ "INDUSTOWER 410 CE - CTC EXIT"

💡 PRO TIP:
These are real intraday options trading signals with specific
strike prices and clear entry/exit instructions.
        """

        guide_file = os.path.join(self.results_dir, "options_trading_guide.txt")
        with open(guide_file, 'w') as f:
            f.write(guide)

        print(f"💾 Options trading guide saved: {guide_file}")

    async def run_options_analysis(self):
        """Run comprehensive options trading analysis"""
        print("🚀 INDIAN OPTIONS TRADING EXTRACTOR")
        print("=" * 50)
        print(f"🎯 Target Group: {self.target_group}")
        print(f"🤖 Available Bot: {self.bot_username}")
        print("=" * 50)

        # Analyze captured content
        signals = self.analyze_captured_content()

        # Create manual guide
        self.create_manual_options_guide()

        print(f"\n✅ Options analysis complete! Check {self.results_dir} for results.")
        return signals

async def main():
    """Main execution"""
    extractor = OptionsTradingExtractor()
    await extractor.run_options_analysis()

if __name__ == "__main__":
    asyncio.run(main())