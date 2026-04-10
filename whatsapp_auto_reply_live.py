#!/usr/bin/env python3
"""
Real-time WhatsApp Auto-Reply Monitor
Watches OpenClaw logs for inbound messages and triggers agent with proper timeout
"""

import asyncio
import subprocess
import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Configuration
WHATSAPP_NUMBER = "+919003349852"
SENDING_NUMBER = "+917977110915"  # Your phone
AGENT_TIMEOUT = 65000  # 65 seconds
LOG_FILE = "/tmp/whatsapp-auto-reply-live.log"

# Colors for output
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"

def log(message, level="INFO"):
    """Log with timestamp and color"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = {
        "INFO": BLUE,
        "SUCCESS": GREEN,
        "ERROR": RED,
        "WARN": YELLOW
    }.get(level, NC)

    print(f"{color}[{timestamp}] {message}{NC}")

    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] [{level}] {message}\n")

async def execute_agent_with_timeout(prompt: str):
    """Execute OpenClaw agent with proper timeout"""
    log(f"🤖 Executing agent (timeout: {AGENT_TIMEOUT/1000}s)")

    start_time = datetime.now()

    proc = await asyncio.create_subprocess_exec(
        'openclaw', 'agent', '--local', '--agent', 'main',
        '--message', prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**dict(os.environ), 'PATH': os.environ.get('PATH', '')}
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=AGENT_TIMEOUT / 1000
        )

        duration = (datetime.now() - start_time).total_seconds()

        if proc.returncode == 0:
            response = stdout.decode().strip()
            # Extract actual response (skip empty lines and metadata)
            lines = [l for l in response.split('\n') if l.strip() and not l.startswith('│')]
            if lines:
                actual_response = '\n'.join(lines)
                log(f"✅ Agent succeeded in {duration:.1f}s", "SUCCESS")
                return {"success": True, "content": actual_response}
            return {"success": True, "content": response}
        else:
            error = stderr.decode().strip()
            log(f"❌ Agent failed: {error[:100]}", "ERROR")
            return {"success": False, "error": error}

    except asyncio.TimeoutError:
        duration = (datetime.now() - start_time).total_seconds()
        log(f"⏱️ Agent timed out after {duration:.1f}s (killed process)", "WARN")
        try:
            proc.kill()
            await asyncio.sleep(0.5)
        except:
            pass
        return {"success": False, "error": f"Timeout after {AGENT_TIMEOUT/1000}s"}

    except Exception as e:
        log(f"❌ Exception: {str(e)}", "ERROR")
        return {"success": False, "error": str(e)}

async def send_whatsapp(target: str, message: str, max_retries: int = 3):
    """Send WhatsApp message via OpenClaw with retry logic"""
    log(f"📤 Sending WhatsApp to {target}: {message[:50]}...")

    for attempt in range(max_retries):
        # Add delay before retry (except first attempt)
        if attempt > 0:
            await asyncio.sleep(2)
            log(f"🔄 Retry attempt {attempt + 1}/{max_retries}...")

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
                timeout=30.0
            )

            if proc.returncode == 0:
                log(f"✅ WhatsApp sent successfully", "SUCCESS")
                return True
            else:
                error = stderr.decode().strip()
                # Check if it's a gateway connection error
                if "gateway closed" in error and attempt < max_retries - 1:
                    log(f"⚠️ Gateway connection lost, retrying...", "WARN")
                    continue
                log(f"❌ WhatsApp failed: {error[:100]}", "ERROR")
                return False

        except asyncio.TimeoutError:
            log(f"❌ WhatsApp timed out", "ERROR")
            if attempt < max_retries - 1:
                continue
            return False

        except Exception as e:
            log(f"❌ Exception: {str(e)}", "ERROR")
            if attempt < max_retries - 1:
                continue
            return False

    log(f"❌ Failed after {max_retries} attempts", "ERROR")
    return False

async def process_inbound_message(message_content: str, sender: str):
    """Process inbound WhatsApp message and send auto-reply"""
    log(f"📬 Received from {sender}: {message_content[:50]}...")

    # Execute agent with timeout
    result = await execute_agent_with_timeout(
        f"You received a WhatsApp message from {sender}: {message_content}\n\nProvide a brief, helpful response."
    )

    if result['success']:
        # Send reply
        response_content = result['content']

        # Clean up response (remove metadata)
        lines = [l for l in response_content.split('\n')
                 if l.strip() and not l.startswith('│') and not l.startswith('◇')]
        clean_response = '\n'.join(lines)[:500]  # Limit to 500 chars

        if not clean_response.strip():
            clean_response = "Message received. I'll get back to you shortly!"

        log(f"📝 Sending reply: {clean_response[:50]}...")
        await send_whatsapp(sender, clean_response)

    else:
        log(f"⚠️ Skipping reply due to error: {result.get('error', 'Unknown')[:50]}", "WARN")

async def monitor_openclaw_logs():
    """Monitor OpenClaw logs for inbound WhatsApp messages"""
    log("=" * 60)
    log("🚀 WhatsApp Auto-Reply Monitor Starting")
    log("=" * 60)
    log(f"📱 Listening for messages to: {WHATSAPP_NUMBER}")
    log(f"👤 Expected sender: {SENDING_NUMBER}")
    log(f"⏱️  Agent timeout: {AGENT_TIMEOUT/1000}s")
    log("=" * 60)
    log("📝 Send a WhatsApp message to trigger auto-reply...")
    log("=" * 60)
    log("")

    # Get today's log file
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = f"/tmp/openclaw/openclaw-{today}.log"

    if not Path(log_file).exists():
        log(f"⚠️  Log file not found: {log_file}")
        log(f"   Will wait for it to be created...")

    # Start tail -f on the log file
    log(f"📂 Monitoring log file: {log_file}")

    proc = await asyncio.create_subprocess_exec(
        'tail', '-F', '-n', '0', log_file,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    log("✅ Monitoring active... Waiting for messages...")
    log("")

    message_count = 0

    try:
        async for line in proc.stdout:
            line_str = line.decode().strip()

            # Look for inbound WhatsApp messages
            # Pattern: "Inbound message +917977110915 -> +919003349852"
            match = re.search(r'Inbound message (\+\d+) -> \+\d+', line_str)

            if match:
                sender = match.group(1)
                message_count += 1

                # Extract message content from the log
                # The body field is in JSON format in the log
                actual_message = None

                # Try to find the message body in recent log entries
                # Format: {"body":"actual message here"}
                body_pattern = re.search(r'"body"\s*:\s*"([^"]+)"', line_str)
                if body_pattern:
                    # Extract and clean the message (remove [WhatsApp...] prefix if present)
                    body_content = body_pattern.group(1)
                    # Remove WhatsApp metadata prefix like "[WhatsApp +917977110915 +10s 2026-02-06 23:38 GMT+5:30] "
                    body_clean = re.sub(r'\[WhatsApp[^\]]*\]\s*', '', body_content)
                    actual_message = body_clean
                else:
                    # Fallback: check for the body in the web-inbound message format
                    # Look for entries with "body":"content" in the log line
                    # We'll need to look at previous lines or use a different approach
                    actual_message = f"WhatsApp message #{message_count}"

                if not actual_message or actual_message == f"WhatsApp message #{message_count}":
                    actual_message = f"WhatsApp message from {sender}"

                log(f"📬 Message #{message_count} from {sender}")
                log(f"   Content: {actual_message[:80]}...")

                # Process the message
                await process_inbound_message(
                    actual_message,
                    sender
                )

                log("─" * 60)

    except asyncio.CancelledError:
        log("\n🛑 Monitoring stopped")

    except Exception as e:
        log(f"❌ Monitor error: {e}", "ERROR")

async def main():
    """Main entry point"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║          WhatsApp Auto-Reply Live Monitor                     ║
║          Powered by TMLPD + OpenClaw                        ║
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
