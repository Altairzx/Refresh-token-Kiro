import asyncio
import base64
import hashlib
import json
import os
import secrets
import ssl
import sys
import time
import uuid
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import aiohttp

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

KIRO_AUTH_BASE = "https://prod.us-east-1.auth.desktop.kiro.dev"
KIRO_LOGIN_ENDPOINT = f"{KIRO_AUTH_BASE}/login"
KIRO_TOKEN_ENDPOINT = f"{KIRO_AUTH_BASE}/oauth/token"
KIRO_REDIRECT_URI = "kiro://kiro.kiroAgent/authenticate-success"

def _generate_pkce_pair() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge

def _extract_code_from_kiro_url(url: str) -> str | None:
    if not url.startswith("kiro://"):
        return None
    params = parse_qs(urlparse(url).query)
    values = params.get("code")
    return values[0] if values else None

async def _wait_for_navigation(page: Any, timeout: int = 10000) -> bool:
    try:
        current_url = page.url
        await page.wait_for_function(
            f'() => window.location.href !== "{current_url}"',
            timeout=timeout
        )
        return True
    except:
        return False

async def _is_password_step(target: Any) -> bool:
    try:
        return bool(await target.evaluate(
            """() => document.querySelectorAll('input[type="password"], input[name="Passwd"]').length > 0"""
        ))
    except:
        return False

async def _is_email_step(target: Any) -> bool:
    try:
        return bool(await target.evaluate(
            """() => document.querySelectorAll('input[type="email"], input[name="identifier"], #identifierId').length > 0"""
        ))
    except:
        return False

async def _fill_and_submit_email(page: Any, email: str) -> bool:
    try:
        await page.fill("#identifierId", email)
        await asyncio.sleep(0.5)
        await page.evaluate('''() => {
            const btn = document.querySelector('#identifierNext button');
            if (btn) btn.click();
        }''')
        await _wait_for_navigation(page, timeout=15000)
        print("[✓] Email submitted", flush=True)
        return True
    except Exception as e:
        print(f"[!] Email error: {e}", flush=True)
        return False

async def _fill_and_submit_password(page: Any, password: str) -> bool:
    try:
        await page.wait_for_selector('input[name="Passwd"]', timeout=10000)
        await asyncio.sleep(1)
        await page.fill('input[name="Passwd"]', password)
        await asyncio.sleep(0.5)
        await page.evaluate('''() => {
            const btn = document.querySelector('#passwordNext button');
            if (btn) btn.click();
        }''')
        await _wait_for_navigation(page, timeout=15000)
        print("[✓] Password submitted", flush=True)
        return True
    except Exception as e:
        print(f"[!] Password error: {e}", flush=True)
        return False

async def _handle_terms_of_service(page: Any) -> bool:
    try:
        if "workspacetermsofservice" not in page.url.lower():
            return False
        clicked = await page.evaluate('''() => {
            const keywords = ['i understand','continue','accept','agree','setuju'];
            for (const btn of document.querySelectorAll('button, div[role="button"], span[role="button"]')) {
                const txt = (btn.textContent || '').trim().toLowerCase();
                if (keywords.some(k => txt.includes(k)) && btn.offsetParent) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }''')
        if clicked:
            await _wait_for_navigation(page, timeout=10000)
            print("[✓] Terms of Service accepted", flush=True)
        return clicked
    except:
        return False

async def _handle_consent(page: Any) -> bool:
    try:
        if "accounts.google.com" not in page.url:
            return False
        clicked = await page.evaluate('''() => {
            const keywords = ['continue','allow','lanjut'];
            for (const btn of document.querySelectorAll('button, div[role="button"]')) {
                const txt = (btn.textContent || '').trim().toLowerCase();
                if (keywords.some(k => txt.includes(k)) && btn.offsetParent) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }''')
        if clicked:
            await _wait_for_navigation(page, timeout=10000)
            print("[✓] Consent bypassed", flush=True)
        return clicked
    except:
        return False

class KiroAuthenticator:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session_state = {}

    async def run(self):
        print(f"\n{'='*60}", flush=True)
        print(f"[START] {self.email}", flush=True)
        print(f"{'='*60}", flush=True)
        
        try:
            from browserforge.fingerprints import Screen
            from camoufox.async_api import AsyncCamoufox
        except ImportError as e:
            print(f"[!] Import error: {e}", flush=True)
            return None

        code_verifier, code_challenge = _generate_pkce_pair()
        self.session_state = {"auth_code": None, "code_verifier": code_verifier}

        manager = AsyncCamoufox(
            headless=True,
            os="windows",
            block_webrtc=True,
            humanize=False,
            screen=Screen(max_width=1920, max_height=1080),
        )
        
        print("[*] Launching browser...", flush=True)
        browser = await manager.__aenter__()
        page = await browser.new_page()
        page.set_default_timeout(20000)
        print("[✓] Browser ready", flush=True)

        def on_response(response: Any) -> None:
            if self.session_state.get("auth_code"):
                return
            try:
                location = response.headers.get("location", "")
                if location.startswith("kiro://"):
                    code = _extract_code_from_kiro_url(location)
                    if code:
                        self.session_state["auth_code"] = code
                        print(f"[✓] Auth code captured: {code[:15]}...", flush=True)
            except:
                pass

        page.on("response", on_response)

        async def route_handler(route: Any) -> None:
            if self.session_state.get("auth_code"):
                await route.continue_()
                return
            url = route.request.url
            if url.startswith("kiro://"):
                code = _extract_code_from_kiro_url(url)
                if code:
                    self.session_state["auth_code"] = code
                    print(f"[✓] Auth code from route: {code[:15]}...", flush=True)
                    await route.abort()
                    return
            await route.continue_()

        await page.route("**/*", route_handler)

        auth_url = f"{KIRO_LOGIN_ENDPOINT}?" + urlencode({
            "idp": "Google",
            "redirect_uri": KIRO_REDIRECT_URI,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": str(uuid.uuid4()),
        })

        print(f"[*] Navigating to Kiro...", flush=True)
        await page.goto(auth_url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        print(f"[✓] Loaded: {page.url[:60]}", flush=True)

        email_filled = False
        password_filled = False
        max_wait = 90  # Kurangi jadi 90 detik

        for attempt in range(max_wait):
            if self.session_state.get("auth_code"):
                print(f"[✓] Success at {attempt}s", flush=True)
                break

            try:
                current_url = page.url
                
                if not email_filled and await _is_email_step(page):
                    print(f"[*] Filling email...", flush=True)
                    if await _fill_and_submit_email(page, self.email):
                        email_filled = True
                        await asyncio.sleep(2)
                        continue
                
                if email_filled and not password_filled and await _is_password_step(page):
                    print(f"[*] Filling password...", flush=True)
                    if await _fill_and_submit_password(page, self.password):
                        password_filled = True
                        await asyncio.sleep(2)
                        continue
                
                if password_filled and await _handle_terms_of_service(page):
                    await asyncio.sleep(2)
                    continue
                
                if password_filled and await _handle_consent(page):
                    await asyncio.sleep(2)
                    continue
                
                if attempt % 10 == 0 and attempt > 0:
                    print(f"[*] Waiting... {attempt}s", flush=True)
                
            except Exception as e:
                print(f"[!] Loop error: {e}", flush=True)
            
            await asyncio.sleep(1)

        await manager.__aexit__(None, None, None)
        print("[✓] Browser closed", flush=True)

        if not self.session_state.get("auth_code"):
            print(f"[✗] Timeout after {max_wait}s", flush=True)
            return None

        return await self.fetch_tokens()

    async def fetch_tokens(self) -> dict:
        code = self.session_state.get("auth_code")
        verifier = self.session_state.get("code_verifier")

        print("[*] Exchanging code for tokens...", flush=True)
        async with aiohttp.ClientSession() as client:
            async with client.post(
                KIRO_TOKEN_ENDPOINT,
                json={"code": code, "code_verifier": verifier, "redirect_uri": KIRO_REDIRECT_URI},
                headers={"Content-Type": "application/json"},
                ssl=_SSL_CTX,
            ) as resp:
                if resp.status == 200:
                    payload = await resp.json()
                    print(f"[✓] Token exchange success", flush=True)
                    return {
                        "access_token": payload.get("accessToken", ""),
                        "refresh_token": payload.get("refreshToken", ""),
                        "profile_arn": payload.get("profileArn", ""),
                        "expires_in": payload.get("expiresIn"),
                        "timestamp": time.time()
                    }
                else:
                    error_text = await resp.text()
                    print(f"[✗] Token exchange failed ({resp.status}): {error_text[:100]}", flush=True)
                return None

def save_tokens_to_json(email: str, token_data: dict, filename="kiro_tokens.json"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    data_store = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data_store = json.load(f)
        except json.JSONDecodeError:
            pass

    data_store[email] = token_data
    with open(filepath, 'w') as f:
        json.dump(data_store, f, indent=2)
    print(f"[✓] Saved to {filepath}", flush=True)

async def process_multiple_accounts(filepath: str):
    if not os.path.exists(filepath):
        print(f"[!] File not found: {filepath}", flush=True)
        return

    # Load existing tokens
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_file = os.path.join(script_dir, "kiro_tokens.json")
    existing_emails = set()
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                existing_emails = set(json.load(f).keys())
        except:
            pass

    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"[*] Total accounts: {len(lines)}", flush=True)
    print(f"[*] Already done: {len(existing_emails)}", flush=True)
    print(f"[*] Remaining: {len(lines) - len(existing_emails)}", flush=True)

    success = 0
    failed = 0

    for i, line in enumerate(lines):
        parts = line.split(':')
        if len(parts) < 2:
            continue
        
        email, password = parts[0].strip(), parts[1].strip()
        
        # Skip if already exists
        if email in existing_emails:
            print(f"\n[{i+1}/{len(lines)}] SKIP: {email} (already exists)", flush=True)
            continue
        
        print(f"\n[{i+1}/{len(lines)}] Processing: {email}", flush=True)
        
        authenticator = KiroAuthenticator(email, password)
        tokens = await authenticator.run()

        if tokens:
            save_tokens_to_json(email, tokens)
            print(f"[✓] SUCCESS: {email}", flush=True)
            success += 1
        else:
            print(f"[✗] FAILED: {email}", flush=True)
            failed += 1
        
        if i < len(lines) - 1:
            wait_time = 10  # Kurangi delay jadi 10 detik
            print(f"[*] Waiting {wait_time}s...", flush=True)
            await asyncio.sleep(wait_time)

    print(f"\n{'='*60}", flush=True)
    print(f"SUMMARY: Success={success}, Failed={failed}, Total={len(existing_emails)+success}", flush=True)
    print(f"{'='*60}", flush=True)

async def main():
    await process_multiple_accounts("accounts.txt")

if __name__ == "__main__":
    asyncio.run(main())
