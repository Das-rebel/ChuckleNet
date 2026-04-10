#!/usr/bin/env python3
"""
Trading Decision Engine - Smart Execution Logic

This module provides intelligent trading decision-making capabilities
that can be integrated with the Telegram Trading Scraper.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class MarketCondition(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"

class TradingAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"

@dataclass
class MarketData:
    """Market data for decision making"""
    current_price: float
    volume_24h: float
    price_change_24h: float
    volatility: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    moving_average: Optional[float] = None

@dataclass
class TradingDecision:
    """Trading decision output"""
    action: TradingAction
    symbol: str
    confidence: float
    position_size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasoning: str
    timestamp: datetime
    market_condition: MarketCondition

class TradingStrategy:
    """Base trading strategy class"""

    def __init__(self, risk_per_trade: float = 0.02, max_drawdown: float = 0.10):
        self.risk_per_trade = risk_per_trade
        self.max_drawdown = max_drawdown
        self.logger = logging.getLogger(__name__)

    def assess_market_condition(self, market_data: MarketData) -> MarketCondition:
        """Assess current market condition"""
        price_change = abs(market_data.price_change_24h)
        volatility = market_data.volatility

        if volatility > 0.05:  # High volatility
            return MarketCondition.VOLATILE
        elif market_data.price_change_24h > 0.02:  # Strong bullish
            return MarketCondition.BULLISH
        elif market_data.price_change_24h < -0.02:  # Strong bearish
            return MarketCondition.BEARISH
        else:
            return MarketCondition.SIDEWAYS

    def calculate_position_size(self, signal_confidence: float,
                              market_condition: MarketCondition) -> float:
        """Calculate position size based on confidence and market conditions"""
        base_size = self.risk_per_trade

        # Adjust for confidence
        confidence_multiplier = 0.5 + (signal_confidence * 0.5)

        # Adjust for market conditions
        condition_multipliers = {
            MarketCondition.BULLISH: 1.2,
            MarketCondition.BEARISH: 1.2,
            MarketCondition.SIDEWAYS: 0.8,
            MarketCondition.VOLATILE: 0.6
        }

        condition_multiplier = condition_multipliers.get(market_condition, 1.0)

        return base_size * confidence_multiplier * condition_multiplier

    def calculate_stop_loss_take_profit(self, current_price: float,
                                      action: TradingAction,
                                      volatility: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        volatility_adjustment = volatility * 2  # 2x volatility for buffer

        if action == TradingAction.BUY:
            stop_loss = current_price * (1 - volatility_adjustment)
            take_profit = current_price * (1 + volatility_adjustment * 2)  # 2:1 R:R
        elif action == TradingAction.SELL:
            stop_loss = current_price * (1 + volatility_adjustment)
            take_profit = current_price * (1 - volatility_adjustment * 2)
        else:
            stop_loss = None
            take_profit = None

        return stop_loss, take_profit

class TradingDecisionEngine:
    """Main trading decision engine"""

    def __init__(self, strategy: TradingStrategy = None):
        self.strategy = strategy or TradingStrategy()
        self.logger = logging.getLogger(__name__)
        self.recent_decisions: List[TradingDecision] = []
        self.daily_loss = 0.0
        self.daily_profit = 0.0

    def make_decision(self, symbol: str, signal_confidence: float,
                     signal_message: str, market_data: MarketData) -> TradingDecision:
        """Make trading decision based on signal and market data"""

        # Assess market condition
        market_condition = self.strategy.assess_market_condition(market_data)

        # Initial action based on signal
        action = self._analyze_signal_action(signal_message)

        # Apply risk management filters
        if self._should_skip_trade(action, signal_confidence, market_condition):
            action = TradingAction.HOLD
            reasoning = "Risk management filters applied - trade skipped"

        # Calculate position size if action is not HOLD
        position_size = 0.0
        stop_loss = None
        take_profit = None

        if action != TradingAction.HOLD:
            position_size = self.strategy.calculate_position_size(signal_confidence, market_condition)
            stop_loss, take_profit = self.strategy.calculate_stop_loss_take_profit(
                market_data.current_price, action, market_data.volatility
            )

        # Generate reasoning
        if action != TradingAction.HOLD:
            reasoning = self._generate_reasoning(
                action, signal_confidence, market_condition, signal_message
            )
        else:
            reasoning = reasoning if 'reasoning' in locals() else "No clear trading signal"

        decision = TradingDecision(
            action=action,
            symbol=symbol,
            confidence=signal_confidence,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            timestamp=datetime.now(),
            market_condition=market_condition
        )

        # Log decision
        self.logger.info(f"🎯 Trading Decision: {action.value} {symbol}")
        self.logger.info(f"   Confidence: {signal_confidence:.2f}")
        self.logger.info(f"   Position Size: {position_size:.2%}")
        self.logger.info(f"   Market Condition: {market_condition.value}")
        self.logger.info(f"   Reasoning: {reasoning}")

        # Store decision
        self.recent_decisions.append(decision)
        self._cleanup_old_decisions()

        return decision

    def _analyze_signal_action(self, signal_message: str) -> TradingAction:
        """Analyze signal message to determine action"""
        message_lower = signal_message.lower()

        buy_keywords = ['buy', 'long', 'enter', '🟢', '✅', '🚀']
        sell_keywords = ['sell', 'short', 'exit', '🔴', '❌', '📉']

        buy_score = sum(1 for keyword in buy_keywords if keyword in message_lower)
        sell_score = sum(1 for keyword in sell_keywords if keyword in message_lower)

        if buy_score > sell_score:
            return TradingAction.BUY
        elif sell_score > buy_score:
            return TradingAction.SELL
        else:
            return TradingAction.HOLD

    def _should_skip_trade(self, action: TradingAction, confidence: float,
                          market_condition: MarketCondition) -> bool:
        """Determine if trade should be skipped based on risk criteria"""

        # Skip if confidence is too low
        if confidence < 0.7:
            return True

        # Skip if market is too volatile for new positions
        if market_condition == MarketCondition.VOLATILE and action != TradingAction.HOLD:
            return True

        # Skip if too many recent trades
        recent_trades = [d for d in self.recent_decisions[-10:] if d.action != TradingAction.HOLD]
        if len(recent_trades) >= 5:
            return True

        # Skip if daily loss limit reached
        if abs(self.daily_loss) >= self.strategy.max_drawdown:
            return True

        return False

    def _generate_reasoning(self, action: TradingAction, confidence: float,
                          market_condition: MarketCondition, signal_message: str) -> str:
        """Generate detailed reasoning for the trading decision"""

        reasoning_parts = []

        # Action reasoning
        if action == TradingAction.BUY:
            reasoning_parts.append("Bullish signal detected")
        elif action == TradingAction.SELL:
            reasoning_parts.append("Bearish signal detected")

        # Confidence reasoning
        if confidence >= 0.8:
            reasoning_parts.append("High confidence signal")
        elif confidence >= 0.7:
            reasoning_parts.append("Moderate confidence signal")

        # Market condition reasoning
        if market_condition == MarketCondition.BULLISH:
            reasoning_parts.append("Favorable bullish market")
        elif market_condition == MarketCondition.BEARISH:
            reasoning_parts.append("Favorable bearish market")
        elif market_condition == MarketCondition.SIDEWAYS:
            reasoning_parts.append("Sideways market - cautious approach")
        elif market_condition == MarketCondition.VOLATILE:
            reasoning_parts.append("High volatility - reduced position size")

        # Signal analysis
        if 'technical' in signal_message.lower():
            reasoning_parts.append("Technical analysis confirmation")
        if 'breakout' in signal_message.lower():
            reasoning_parts.append("Breakout pattern identified")
        if 'support' in signal_message.lower() or 'resistance' in signal_message.lower():
            reasoning_parts.append("Key level identified")

        return "; ".join(reasoning_parts)

    def _cleanup_old_decisions(self):
        """Remove decisions older than 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.recent_decisions = [
            d for d in self.recent_decisions
            if d.timestamp > cutoff_time
        ]

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        recent_trades = [d for d in self.recent_decisions if d.action != TradingAction.HOLD]

        if not recent_trades:
            return {
                'total_trades': 0,
                'avg_confidence': 0,
                'success_rate': 0,
                'profit_loss': 0
            }

        total_trades = len(recent_trades)
        avg_confidence = sum(d.confidence for d in recent_trades) / total_trades

        # This would be calculated based on actual trade results
        # For now, using placeholder logic
        success_rate = min(0.65, avg_confidence * 0.8)  # Conservative estimate

        return {
            'total_trades': total_trades,
            'avg_confidence': avg_confidence,
            'success_rate': success_rate,
            'profit_loss': self.daily_profit - self.daily_loss,
            'recent_decisions_count': len(self.recent_decisions)
        }

# Example usage and integration with Telegram scraper
def example_usage():
    """Example of how to use the trading decision engine"""

    # Initialize the engine
    engine = TradingDecisionEngine()

    # Example market data (would come from your trading API)
    market_data = MarketData(
        current_price=50000.0,
        volume_24h=1000000000,
        price_change_24h=0.025,  # 2.5% up
        volatility=0.03,  # 3% volatility
        rsi=65.0,
        macd=100.0
    )

    # Example signal from Telegram
    signal_message = "🟢 BTC showing strong bullish momentum above resistance at $49,800 with confirmed technical analysis"
    signal_confidence = 0.85

    # Make decision
    decision = engine.make_decision(
        symbol="BTC",
        signal_confidence=signal_confidence,
        signal_message=signal_message,
        market_data=market_data
    )

    print(f"Decision: {decision.action.value}")
    print(f"Position Size: {decision.position_size:.2%}")
    print(f"Stop Loss: ${decision.stop_loss:,.2f}")
    print(f"Take Profit: ${decision.take_profit:,.2f}")
    print(f"Reasoning: {decision.reasoning}")

    # Get performance stats
    stats = engine.get_performance_stats()
    print(f"Performance: {stats}")

if __name__ == "__main__":
    example_usage()