# -*- coding: utf-8 -*-
#
# KTMB Auto Ticket Bot
# Copyright (C) 2025 AnnChongS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import time
import requests
import json
import os
from datetime import datetime
from playwright.sync_api import Playwright, sync_playwright, expect

# ================= 🔧 配置加载模块 =================
CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f">>> [错误] 找不到配置文件 {CONFIG_FILE}")
        os._exit(1)
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        print(f">>> [错误] 读取配置文件出错: {e}")
        os._exit(1)

CFG = load_config()

KTMB_EMAIL = CFG.get("account", {}).get("email", "")
KTMB_PASSWORD = CFG.get("account", {}).get("password", "")

BOT_ID = CFG.get("bot_settings", {}).get("bot_id", "1")
BOT_NAME = f"Commander-{BOT_ID}"
CHROME_DEBUG_PORT = CFG.get("bot_settings", {}).get("chrome_port", 9222)
HEARTBEAT_INTERVAL = CFG.get("bot_settings", {}).get("heartbeat_interval", 100)
REFRESH_INTERVAL = CFG.get("bot_settings", {}).get("refresh_interval", 180)

TELEGRAM_BOT_TOKEN = CFG.get("notification", {}).get("telegram_token", "")
TELEGRAM_CHAT_ID = CFG.get("notification", {}).get("telegram_chat_id", "")
HEARTBEAT_SCREENSHOT = CFG.get("notification", {}).get("heartbeat_screenshot", False)

SEARCH_CONFIGS = CFG.get("search_tasks", [])
PAYMENT_METHOD = CFG.get("payment_method", "Command")

PREFER_FORWARD = CFG.get("preferences", {}).get("prefer_forward", True)
PREFER_WINDOW = CFG.get("preferences", {}).get("prefer_window", True)
PREFER_NORMAL_SEAT = CFG.get("preferences", {}).get("prefer_normal_seat", True)
ACCEPT_TABLE_SEAT = CFG.get("preferences", {}).get("accept_table_seat", True)

SHOULD_LOGOUT_AND_EXIT = False

# ==========================================================

def send_notification(message):
    current_time = datetime.now().strftime('%H:%M:%S')
    formatted_msg = f"<b>[{BOT_NAME}] {current_time}</b>\n{message}"
    print(f">>> [TG通知] 已推送到手机...")
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": formatted_msg, "parse_mode": "HTML"}
            requests.post(url, data=data, timeout=5)
        except: pass

def send_telegram_photo(caption, image_bytes):
    current_time = datetime.now().strftime('%H:%M:%S')
    formatted_caption = f"<b>[{BOT_NAME}] {current_time}</b>\n{caption}"
    print(f">>> [TG通知] 正在发送屏幕截图...")
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            files = {'photo': image_bytes}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": formatted_caption, "parse_mode": "HTML"}
            requests.post(url, data=data, files=files, timeout=20)
        except: pass

def flush_telegram_updates():
    """清空之前的历史指令，防止一开机就执行以前的 /logout 导致自杀"""
    if not TELEGRAM_BOT_TOKEN: return None
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        resp = requests.get(url, timeout=5).json()
        if resp["ok"] and len(resp["result"]) > 0:
            return resp["result"][-1]["update_id"] + 1
    except: pass
    return None

def check_telegram_command(offset=None):
    global SHOULD_LOGOUT_AND_EXIT
    if not TELEGRAM_BOT_TOKEN: return None, None, offset
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"timeout": 0, "allowed_updates": ["message"]}
        if offset: params["offset"] = offset
        
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        
        if data["ok"] and len(data["result"]) > 0:
            last_update = data["result"][-1]
            new_offset = last_update["update_id"] + 1
            if "message" in last_update and "text" in last_update["message"]:
                text = last_update["message"]["text"].strip().lower()
                parts = text.split()
                command = parts[0].split('@')[0] 
                target_id = parts[1] if len(parts) > 1 else "all"
                if len(parts) == 1 and text[-1].isdigit():
                    target_id = text[-1]
                    command = text[:-1]
                
                if command == "/logout" and (target_id == "all" or target_id == BOT_ID):
                    SHOULD_LOGOUT_AND_EXIT = True
                    
                return command, target_id, new_offset
            return None, None, new_offset
    except: pass
    return None, None, offset

def handle_popup(page):
    time.sleep(0.5)
    try:
        if page.locator("#popupModal").is_visible():
            if page.locator("#popupModalCloseButton").is_visible(): page.locator("#popupModalCloseButton").click()
            elif page.locator("#popupModalOkButton").is_visible(): page.locator("#popupModalOkButton").click()
            elif page.locator("#popupModalCancelButton").is_visible(): page.locator("#popupModalCancelButton").click()
            page.evaluate("document.getElementById('popupModal').style.display = 'none';")
            page.evaluate("if(document.querySelector('.modal-backdrop')) document.querySelector('.modal-backdrop').remove();")
        elif page.locator(".modal-content:visible").count() > 0:
            page.locator("button.close, button:has-text('Close')").click()
    except: pass

def safe_logout(page):
    print(">>> [系统] 收到退出指令，正在执行安全登出(Logout)...")
    try:
        if not page.locator("#navbarFileDropdown").first.is_visible():
            page.goto("https://online.ktmb.com.my/", timeout=15000)
            
        if page.locator("#navbarFileDropdown").first.is_visible():
            page.locator("#navbarFileDropdown").first.click(force=True)
            time.sleep(1)
            logout_btn = page.locator("a.dropdown-item[href='/Account/Logout']")
            if logout_btn.count() > 0:
                logout_btn.first.click(force=True)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                print(">>> [系统] 登出成功！")
                send_notification("✅ 已精准安全退出 KTMB 账号，告别 30 分钟冷却。程序即将关闭。")
            else:
                page.goto("https://online.ktmb.com.my/Account/Logout", timeout=10000)
                send_notification("✅ 已通过后门网址强行登出。程序安全关闭。")
        else:
            print(">>> [系统] 当前未登录，无需登出。")
            send_notification("✅ 当前未登录，程序安全关闭。")
    except Exception as e:
        print(f">>> [错误] 安全登出失败: {e}")
        send_notification(f"⚠️ 尝试安全退出失败: {e}")

def ensure_on_homepage(page):
    current_url = page.url
    target_url = "https://online.ktmb.com.my/"
    if current_url == target_url or current_url == target_url + "Home/Index":
        handle_popup(page)
        return
    print(f">>> [导航] 跳转回主页...")
    try:
        page.goto(target_url, timeout=30000)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        handle_popup(page)
    except: pass

def login(page):
    page.set_viewport_size({"width": 1920, "height": 1080})
    try:
        if "Login" not in page.url:
            page.goto("https://online.ktmb.com.my/Account/Login", timeout=30000)
    except: pass
    
    start_time = time.time()
    while time.time() - start_time < 15:
        handle_popup(page)
        if page.locator("a[href*='/Account/Login']").is_visible():
            print(">>> [系统] 执行登录...")
            try:
                page.locator("a[href*='/Account/Login']").click()
                page.get_by_role("textbox", name="Email").fill(KTMB_EMAIL)
                page.get_by_role("textbox", name="Password").fill(KTMB_PASSWORD)
                page.get_by_role("button", name="Login").click()
                page.wait_for_url("https://online.ktmb.com.my/", timeout=15000)
                print(">>> [系统] 登录成功")
                return
            except Exception as e:
                print("    [警告] 登录异常，重试...")
                handle_popup(page)
                time.sleep(2)
                
        if page.locator("#navbarFileDropdown").first.is_visible():
            return
        time.sleep(1)

    print(">>> [错误] 登录超时。")
    try: page.context.clear_cookies() 
    except: pass

def perform_search(page, config):
    date_str = f"{config['year']}-{config['month']}-{config['day']}"
    print(f">>> [搜索] 计划: {date_str} {config['time']}")
    
    time.sleep(1)
    page.locator("#select2-FromStationId-container").click(timeout=15000)
    page.get_by_role("option", name=config['from']).click()
    page.locator("#select2-ToStationId-container").click()
    page.get_by_role("option", name=config['to']).click()
    
    try:
        depart_input = page.get_by_role("textbox", name="Depart")
        depart_input.evaluate("node => { node.scrollIntoView(); node.click(); }")
        page.wait_for_selector(".lightpick__select-years", state="visible", timeout=3000)
    except:
        print("    [提示] 日历似乎未弹出，清理弹窗后重试...")
        handle_popup(page) 
        time.sleep(0.5)
        try:
            depart_input = page.get_by_role("textbox", name="Depart")
            depart_input.click(force=True)
            page.wait_for_selector(".lightpick__select-years", state="visible", timeout=5000)
        except Exception as e:
            print("    [错误] 网页卡顿，日历无法打开，跳过...")
            try:
                error_shot = page.screenshot(type='png', full_page=True)
                send_telegram_photo("⚠️ <b>日历弹出失败！</b>", error_shot)
            except: pass
            return False 
            
    max_retries = 12
    for _ in range(max_retries):
        cy = int(page.locator(".lightpick__select-years").input_value())
        cm = int(page.locator(".lightpick__select-months").input_value()) + 1
        if cy > config['year'] or (cy == config['year'] and cm >= config['month']): break
        page.locator(".lightpick__next-action").click(); time.sleep(0.3)
    
    day_str = str(config['day'])
    page.locator(f".lightpick__day:not(.is-next-month):not(.is-previous-month):text-is('{day_str}')").click()
    page.get_by_role("button", name="SEARCH").click()

    try: page.wait_for_selector(".btn-seat-layout", timeout=8000)
    except: print("    [结果] 无车次"); return False
    
    handle_popup(page)
    target_btn = page.locator(f"tr:has-text('{config['time']}') .btn-seat-layout")
    
    if target_btn.count() > 0:
        print("    [发现] 目标车次！")
        if page.locator("#popupModal").is_visible(): handle_popup(page)
        try: target_btn.first.click(timeout=5000)
        except: handle_popup(page); target_btn.first.click(force=True)
        return True
    else:
        print("    [结果] 车次未找到")
        return False

def select_seat(page, is_old_train):
    print(">>> [操作] 正在选座...")
    try: page.wait_for_selector("#seatSelect", state="visible", timeout=15000)
    except: return False
    
    coach_buttons = page.locator(".coache-btn")
    for i in range(coach_buttons.count()):
        btn = coach_buttons.nth(i)
        if "active" not in btn.get_attribute("class"): 
            btn.click()
            time.sleep(0.5)
        
        seat = None
        if is_old_train:
            base_sel = "img.selectable-icon:visible:not([src*='Selected']):not([src*='Occupied'])[data-seat-service-type='Standard']"
            dir_sel = ":is([src*='Foward'], [src*='Forward'])" if PREFER_FORWARD else "[src*='Backward']"
            win_sel = "[src*='Win']" if PREFER_WINDOW else ":not([src*='Win'])"
            
            seat = page.locator(f"{base_sel}{dir_sel}{win_sel}").first
            if not seat or seat.count() == 0: seat = page.locator(f"{base_sel}{dir_sel}").first
            if not seat or seat.count() == 0 and PREFER_WINDOW: seat = page.locator(f"{base_sel}{win_sel}").first
            if not seat or seat.count() == 0: seat = page.locator(f"{base_sel}").first
        else:
            if PREFER_NORMAL_SEAT: seat = page.locator("img.selectable-icon[src*='StanFor']:visible").first
            if not seat and ACCEPT_TABLE_SEAT: seat = page.locator("img.selectable-icon[src*='StanClus']:visible").first
        
        if seat and seat.is_visible():
            try:
                seat.click()
                time.sleep(0.5)
                confirm = page.locator("#confirmSeatBtn")
                if "disabled-btn" not in confirm.get_attribute("class"):
                    confirm.click()
                    print(">>> [成功] 选座成功！")
                    return True
                else:
                    confirm.click()
                    return True
            except: pass
            
    try: page.locator("#seatSelect .close").click()
    except: pass
    return False

def extract_ticket_info(page):
    try:
        page.wait_for_selector(".station_detail", timeout=5000)
        train_info_el = page.locator(".station_detail .c444.mt5.fw100.f17").first
        train_info_text = train_info_el.inner_text().strip() if train_info_el.is_visible() else "未知"
        seat_info_el = page.locator(".col-lg-4 p.f12.mt10").first
        seat_info_text = seat_info_el.inner_text().strip() if seat_info_el.is_visible() else "未知"
        price_el = page.locator("tr.f14 td.text-right b").first
        price_text = price_el.inner_text().strip() if price_el.is_visible() else "未知"
        return f"🎫 票务确认\n🚆 {train_info_text}\n💺 {seat_info_text}\n💰 {price_text}"
    except:
        return "详情抓取失败"

def execute_payment_command(page, context, command, target_id):
    if target_id != "all" and target_id != BOT_ID: return False
    print(f">>> [指令] 收到支付指令: {command}")
    if command == "/manual":
        send_notification("🛑 已切换人工模式。")
        return True
    try:
        if command == "/duitnow":
            send_notification("💳 正在生成 DuitNow...")
            page.locator("#btnGoPaymentDuitNow").click()
            proceed_btn = page.locator("input[value*='Click HERE'], input[type='submit']").first
            proceed_btn.wait_for(state="visible", timeout=15000)
            with context.expect_page() as new_page_info: proceed_btn.click()
            gateway_page = new_page_info.value
            gateway_page.wait_for_load_state("domcontentloaded")
            time.sleep(8)
            gateway_page.set_viewport_size({"width": 1920, "height": 2500})
            time.sleep(1)
            try: gateway_page.evaluate("window.scrollBy(0, 400)")
            except: pass
            screenshot = gateway_page.screenshot(type='png', full_page=True)
            send_telegram_photo("⚡️ DuitNow 请扫码", screenshot)
            send_notification(f"🔗 链接:\n{gateway_page.url}")
            return False

        elif command == "/tng":
            send_notification("💳 正在生成 TnG...")
            page.locator("#btnGoPaymentTnG").click()
            proceed_btn = page.locator("input[value*='Click HERE'], input[type='submit']").first
            proceed_btn.wait_for(state="visible", timeout=15000)
            with context.expect_page() as new_page_info: proceed_btn.click()
            gateway_page = new_page_info.value
            try:
                gateway_page.wait_for_selector("#submitButton", state="visible", timeout=20000)
                gateway_page.locator("#submitButton").click()
            except: pass
            time.sleep(5)
            gateway_page.set_viewport_size({"width": 1920, "height": 2500})
            time.sleep(1)
            try: gateway_page.evaluate("window.scrollBy(0, 400)")
            except: pass
            screenshot = gateway_page.screenshot(type='png', full_page=True)
            send_telegram_photo("⚡️ TnG 请扫码", screenshot)
            return False
            
        elif command == "/wallet":
            send_notification("💳 尝试 KTM Wallet...")
            page.locator("#btnKtmbEWallet").click()
            time.sleep(3)
            if page.locator("#popupModal:has-text('insufficient')").is_visible():
                send_notification("⚠️ 余额不足！请换方式。")
                if page.locator("#popupModalCloseButton").is_visible(): page.locator("#popupModalCloseButton").click()
                elif page.locator("#popupModalOkButton").is_visible(): page.locator("#popupModalOkButton").click()
                elif page.locator("#popupModalCancelButton").is_visible(): page.locator("#popupModalCancelButton").click()
                try: page.locator("#popupModal").wait_for(state="hidden", timeout=3000)
                except: pass
                return False
            else:
                send_notification("✅ Wallet 扣款已发送。")
                return True

    except Exception as e:
        send_notification(f"⚠️ 指令异常: {e}")
    return False

def wait_for_payment_command(page, context):
    print(">>> [系统] 进入待命模式...")
    ticket_info = extract_ticket_info(page)
    msg = (
        f"🚨 <b>{BOT_NAME} 抢票成功！</b> 🚨\n\n{ticket_info}\n\n"
        f"👇 <b>请发送指令：</b>\n/duitnow{BOT_ID} | /tng{BOT_ID} | /wallet{BOT_ID} | /manual{BOT_ID}"
    )
    send_notification(msg)
    
    _, _, last_offset = check_telegram_command(offset=None)
    for _ in range(400):
        time.sleep(3)
        command, target_id, new_offset = check_telegram_command(offset=last_offset)
        if command:
            last_offset = new_offset 
            if execute_payment_command(page, context, command, target_id):
                print(">>> [系统] 流程结束。"); return True 
            else:
                if target_id == "all" or target_id == BOT_ID:
                    send_notification(f"🤖 仍在待命...")
        try:
            if not page.url.startswith("https"): break
        except: break
    return True

def process_automated_payment(page, context, method):
    if method == "Manual":
        send_notification("🛑 请手动付款！")
        time.sleep(1800)
        return True
    if method == "KTM Wallet":
        return execute_payment_command(page, context, "/wallet", "all")
    if method == "DuitNow":
        execute_payment_command(page, context, "/duitnow", "all")
        time.sleep(1800)
        return True
    return False

def handle_passenger_and_payment(page, context, is_old_train):
    try:
        page.locator(".btn-passenger").click()
        page.wait_for_selector(".IsSelf", state="visible", timeout=30000)
        page.locator(".IsSelf").check()
        time.sleep(1.5)
        page.locator("select.TicketTypeId").select_option(value="Adult")
        page.locator("#btnConfirmPayment").click()
        if not is_old_train:
            try:
                page.locator("#btnUpdateInsuranceNo").click()
                page.locator("#popupModalOkButton").click()
            except: pass
            try:
                page.locator("#btnProceedToPayment").click()
                page.locator("#confirmationConfirmButton").click()
            except: pass
        page.wait_for_url(lambda u: "/Book" in u, timeout=30000)
        if PAYMENT_METHOD == "Command":
            return wait_for_payment_command(page, context)
        else:
            return process_automated_payment(page, context, PAYMENT_METHOD)
    except Exception as e:
        print(f">>> [异常] 填表流程出错: {e}")
        return False

def run(playwright: Playwright) -> None:
    global SHOULD_LOGOUT_AND_EXIT
    
    # 开机立刻清空历史 Telegram 指令，防止一开机就执行以前的 /logout 导致自杀
    tg_offset = flush_telegram_updates()
    
    print(f">>> [连接] Chrome (Port {CHROME_DEBUG_PORT})...")
    try:
        browser = playwright.chromium.connect_over_cdp(f"http://localhost:{CHROME_DEBUG_PORT}")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
    except Exception as e:
        print(f">>> [错误] 浏览器连接失败: {e}")
        return

    send_notification("🤖 机器人启动 | 模式: " + PAYMENT_METHOD)

    try:
        total_loop = 0
        while True:
            if SHOULD_LOGOUT_AND_EXIT:
                safe_logout(page)
                break

            total_loop += 1
            print(f"\n>>> [进度] 第 {total_loop} 轮大循环 ({datetime.now().strftime('%H:%M:%S')})")
            
            if total_loop % HEARTBEAT_INTERVAL == 0:
                tasks_info = "".join([f"- {cfg['month']}月{cfg['day']}日 {cfg['time']}\n" for cfg in SEARCH_CONFIGS])
                msg = f"💓 存活确认\n轮数: {total_loop}\n任务:\n{tasks_info}"
                
                if HEARTBEAT_SCREENSHOT:
                    try:
                        screenshot = page.screenshot(type='png')
                        send_telegram_photo(msg, screenshot)
                    except Exception as e:
                        send_notification(msg + f"\n(⚠️ 截图失败: {e})")
                else:
                    send_notification(msg)

            for config in SEARCH_CONFIGS:
                if SHOULD_LOGOUT_AND_EXIT: break
                
                try:
                    ensure_on_homepage(page)
                    login(page)
                    is_old_train = config.get("is_old_train", False)
                    
                    if perform_search(page, config):
                        if select_seat(page, is_old_train):
                            if handle_passenger_and_payment(page, context, is_old_train):
                                print(">>> [完成] 任务成功退出。")
                                return 
                            else:
                                print("    [中断] 付款中断...")
                        else:
                            print("    [失败] 座位被抢空")
                except Exception as e:
                    print(f"    [致命异常] 流程崩溃: {e}")
                    try:
                        error_shot = page.screenshot(type='png', full_page=True)
                        send_telegram_photo(f"⚠️ <b>报告！遇到卡死报错</b>\n错误详情: <code>{str(e)[:150]}...</code>", error_shot)
                    except: pass
            
            if SHOULD_LOGOUT_AND_EXIT: break

            print(f">>> [休息] 倒计时 {REFRESH_INTERVAL} 秒...")
            for i in range(REFRESH_INTERVAL, 0, -1):
                if SHOULD_LOGOUT_AND_EXIT: break
                
                if i % 10 == 0 or i <= 5: 
                    print(f"    剩余 {i} 秒...", end="\r")
                
                if i % 3 == 0:
                    command, target_id, new_offset = check_telegram_command(offset=tg_offset)
                    if command:
                        tg_offset = new_offset 
                        if command == "/snap" and (target_id == "all" or target_id == BOT_ID):
                            print("\n>>> [指令] 收到 /snap，正在截图汇报...")
                            try:
                                screenshot = page.screenshot(type='png', full_page=True)
                                send_telegram_photo("📸 <b>长官，这是现在的监控画面</b>", screenshot)
                            except: pass

                time.sleep(1)
            print("")

    except KeyboardInterrupt:
        print(">>> [系统] 收到 Ctrl+C，准备退出...")
    finally:
        try: browser.close()
        except: pass

with sync_playwright() as playwright:
    run(playwright)
