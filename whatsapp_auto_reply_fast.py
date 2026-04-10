#!/usr/bin/env python3
"""
FAST WhatsApp Auto-Reply - Optimized for Speed
Uses fast models and quick responses
"""

import asyncio
import subprocess
import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration - OPTIMIZED FOR SPEED
WHATSAPP_NUMBER = "+919003349852"
SENDING_NUMBER = "+917977110915"
AGENT_TIMEOUT = 25000  # 25 seconds (was 65!)
LOG_FILE = "/tmp/whatsapp-auto-reply-live.log"

# Fast model selection
USE_FAST_MODEL = True  # Use gemini-flash for all queries
FAST_MODEL = "google/gemini-2.5-flash"  # Fastest reliable model

# Colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
NC = "\033[0m"

def log(message, level="INFO"):
    """Log with timestamp and color"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = {
        "INFO": BLUE,
        "SUCCESS": GREEN,
        "ERROR": RED,
        "WARN": YELLOW,
        "FAST": CYAN,
    }.get(level, NC)

    print(f"{color}[{timestamp}] {message}{NC}")

    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] [{level}] {message}\n")


async def execute_agent_fast(prompt: str, sender: str) -> Dict[str, Any]:
    """Execute agent with FAST model"""
    log(f"📬 From {sender}: {prompt[:50]}...", "INFO")
    log(f"⚡ Using FAST model: {FAST_MODEL}", "FAST")

    start_time = datetime.now()

    proc = await asyncio.create_subprocess_exec(
        'openclaw', 'agent', '--local', '--agent', 'main',
        '--message', prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={
            **dict(os.environ),
            'PATH': os.environ.get('PATH', ''),
            'OPENCLAW_MODEL': FAST_MODEL,  # Override model
        }
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=AGENT_TIMEOUT / 1000
        )

        duration = (datetime.now() - start_time).total_seconds()

        if proc.returncode == 0:
            response = stdout.decode().strip()
            # Clean up response - remove table borders
            lines = [l for l in response.split('\n')
                     if l.strip() and not l.startswith('│') and not l.startswith('◇')]
            if lines:
                actual_response = '\n'.join(lines)
            else:
                actual_response = response

            # Truncate to 300 chars for WhatsApp
            clean_response = actual_response[:300]

            log(f"✅ Response in {duration:.1f}s", "SUCCESS")
            log(f"📝 Reply: {clean_response[:50]}...", "INFO")
            return {"success": True, "content": clean_response, "source": "fast"}
        else:
            error = stderr.decode().strip()
            log(f"❌ Agent failed: {error[:100]}", "ERROR")
            return {"success": False, "error": error}

    except asyncio.TimeoutError:
        duration = (datetime.now() - start_time).total_seconds()
        log(f"⏱️ Timeout after {duration:.1f}s", "WARN")
        try:
            proc.kill()
            await asyncio.sleep(0.5)
        except:
            pass
        return {"success": False, "error": f"Timeout after {AGENT_TIMEOUT/1000}s"}

    except Exception as e:
        log(f"❌ Exception: {str(e)}", "ERROR")
        return {"success": False, "error": str(e)}


async def send_whatsapp(target: str, message: str, max_retries: int = 2):
    """Send WhatsApp message via OpenClow"""
    log(f"📤 Sending to {target}: {message[:50]}...")

    for attempt in range(max_retries):
        if attempt > 0:
            await asyncio.sleep(1)
            log(f"🔄 Retry {attempt + 1}/{max_retries}...", "WARN")

        proc = await asyncio.create_subprocess_exec(
            'openclaw', 'message', 'send',
            '--channel', 'whatsapp',
            '--target', target,
            '--message', message,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**dict(os.environ), 'PATH': os.environ.get('PATH', '')}
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=20.0  # 20 second timeout for sending
            )

            if proc.returncode == 0:
                log(f"✅ Sent successfully", "SUCCESS")
                return True
            else:
                error = stderr.decode().strip()
                if "gateway closed" in error and attempt < max_retries - 1:
                    log(f"⚠️ Gateway error, retrying...", "WARN")
                    continue
                log(f"❌ Send failed: {error[:100]}", "ERROR")
                return False

        except asyncio.TimeoutError:
            log(f"❌ Send timeout", "ERROR")
            if attempt < max_retries - 1:
                continue
            return False

        except Exception as e:
            log(f"❌ Exception: {str(e)}", "ERROR")
            if attempt < max_retries - 1:
                continue
            return False

    return False


async def process_inbound_message(message_content: str, sender: str):
    """Process inbound WhatsApp message with FAST model"""
    # For simple queries, use even shorter response
    simple_responses = {
        'hello': 'Hey! 👋 How can I help you today?',
        'hi': 'Hi there! 👋 What can I do for you?',
        'hey': 'Hey! What\'s up?',
        'thanks': 'You\'re welcome! 🙏',
        'thank you': 'Happy to help! 😊',
        'ok': 'Got it! 👍',
        'bye': 'See you later! 👋',
        'goodbye': 'Take care! 👋',
    }

    # Check for simple greetings
    content_lower = message_content.strip().lower()
    for key, response in simple_responses.items():
        if key in content_lower and len(content_lower) < 20:
            log(f"🎯 Quick match: '{key}'", "FAST")
            await send_whatsapp(sender, response)
            return

    # For other messages, use AI (but FAST)
    result = await execute_agent_fast(
        f"Reply to this WhatsApp message concisely (max 2-3 sentences): {message_content}",
        sender
    )

    if result['success']:
        await send_whatsapp(sender, result['content'])
    else:
        log(f"⚠️ Skipping reply due to error", "WARN")


async def monitor_openclaw_logs():
    """Monitor OpenClow logs for inbound WhatsApp messages"""
    log("=" * 60)
    log("⚡ FAST WhatsApp Auto-Reply")
    log("=" * 60)
    log(f"📱 Listening for messages to: {WHATSAPP_NUMBER}")
    log(f"⚡ Fast Model: {FAST_MODEL}")
    log(f"⏱️  Timeout: {AGENT_TIMEOUT/1000}s (was 65s!)")
    log(f"🎯 Simple queries: Instant response")
    log("=" * 60)
    log("📝 Send a WhatsApp message to test...")
    log("=" * 60)
    log("")

    today = datetime.now().strftime('%Y-%m-%d')
    log_file = f"/tmp/openclaw/openclaw-{today}.log"

    if not Path(log_file).exists():
        log(f"⚠️  Log file not found: {log_file}")
        log(f"   Will wait for it to be created...")

    log(f"📂 Monitoring log file: {log_file}")

    proc = await asyncio.create_subprocess_exec(
        'tail', '-F', '-n', '0', log_file,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    log("✅ Monitoring active...")

    message_count = 0

    try:
        async for line in proc.stdout:
            line_str = line.decode().strip()

            # Try multiple patterns to detect inbound messages
            match = None
            sender = None
            actual_message = None

            # Pattern 1: Traditional format
            match = re.search(r'Inbound message (\+\d+) -> \+\d+', line_str)

            # Pattern 2: JSON format
            if not match:
                json_match = re.search(r'"from"\s*:\s*"(\+\d+)"', line_str)
                if json_match:
                    sender = json_match.group(1)
                    if re.search(r'"to"\s*:\s*"\+919003349852"', line_str):
                        match = json_match

            # Pattern 3: web-inbound format
            if not match:
                if re.search(r'web-inbound.*inbound message', line_str, re.IGNORECASE):
                    json_match = re.search(r'"from"\s*:\s*"(\+\d+)"', line_str)
                    if json_match:
                        sender = json_match.group(1)
                        match = json_match

            if match:
                if not sender:
                    sender = match.group(1)
                message_count += 1

                body_pattern = re.search(r'"body"\s*:\s*"([^"]+)"', line_str)
                if body_pattern:
                    body_content = body_pattern.group(1)
                    body_clean = re.sub(r'\[WhatsApp[^\]]*\]\s*', '', body_content)
                    actual_message = body_clean
                else:
                    actual_message = f"WhatsApp message #{message_count}"

                if not actual_message or actual_message == f"WhatsApp message #{message_count}":
                    actual_message = f"WhatsApp message from {sender}"

                log(f"📬 Message #{message_count} from {sender}")
                log(f"   Content: {actual_message[:80]}...")

                await process_inbound_message(actual_message, sender)

                log("─" * 60)

    except asyncio.CancelledError:
        log("\n🛑 Monitoring stopped")

    except Exception as e:
        log(f"❌ Monitor error: {e}", "ERROR")


async def main():
    """Main entry point"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║         ⚡ FAST WhatsApp Auto-Reply ⚡                    ║
║         Optimized for Speed (25s timeout)                  ║
╚════════════════════════════════════════════════════════════════╝
    """)

    try:
        await monitor_openclaw_logs()
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
        log("Monitoring stopped by user")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
