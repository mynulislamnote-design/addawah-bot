import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# --- কনফিগারেশন (এখন আর কোডে সরাসরি Key থাকবে না, Render সার্ভার থেকে আসবে) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "addawah_bot_2026")

def load_products():
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return[]

products = load_products()

@app.route('/', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print("\n--- Facebook Verification ---")
    print(f"EAAOA3Btgb08BRZAuu81Ld5pUTNFw0eQDT3NZBMn9wAVh9s6IN59WvZBWJVY2gxf6JQhDCgZCie4fo39u5GFoVnVGhhTA2BPJ8EmaIzRxwsgd2TiyuUsZBIdLHJHNr5mbZAqAIieXqKeJanOVDmPbl5zw3oRBpZBteLnF46TTgN07yUhKxW5GZAmtsMKtTiOZA47biPdTA: '{token}'")
    print(f"addawah_bot_2026: '{VERIFY_TOKEN}'")
    print("-----------------------------\n")
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return "Failed", 403

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json(silent=True) or {}
    if data.get('object') == 'page':
        for entry in data.get('entry',[]):
            for messaging_event in entry.get('messaging',[]):
                if messaging_event.get('message') and not messaging_event['message'].get('is_echo'):
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text', '')
                    if message_text:
                        print(f"\n[+] কাস্টমার মেসেজ দিয়েছে: {message_text}")
                        handle_message(sender_id, message_text)
    return "OK", 200

def handle_message(sender_id, user_text):
    system_instruction = f"""
    তুমি 'আদ দাওয়া ডিজিটাল পাবলিকেশন'-এর একজন অত্যন্ত বিনয়ী এবং দক্ষ কাস্টমার সাপোর্ট বট। 
    তোমার কাছে নিচের প্রোডাক্ট লিস্ট আছে:
    {json.dumps(products, ensure_ascii=False)}
    
    তোমার দায়িত্ব:
    ১. কাস্টমার প্রোডাক্ট সম্পর্কে জানতে চাইলে সুন্দর করে বিস্তারিত বলবে।
    ২. কাস্টমার বাংলা, ইংরেজি বা বাংলিশ যে ভাষাতেই প্রশ্ন করুক, তুমি সেই ভাষাতেই উত্তর দেবে।
    ৩. কেউ অর্ডার করতে চাইলে তার কাছ থেকে সম্পূর্ণ নাম, মোবাইল নাম্বার এবং পূর্ণাঙ্গ ঠিকানা চাইবে।
    ৪. সব তথ্য পেলে বলবে "ধন্যবাদ, আপনার অর্ডারটি কনফার্ম করার জন্য আমাদের টিম শীঘ্রই যোগাযোগ করবে।"
    ৫. উত্তরগুলো খুব বেশি বড় করবে না, মেসেঞ্জারে পড়ার মতো ছোট ও গোছানো রাখবে।
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts":[
                {"text": system_instruction},
                {"text": f"কাস্টমারের মেসেজ: {user_text}\nবটের রিপ্লাই:"}
            ]
        }]
    }
    
    print("[*] জেমিনি এপিআই-এর কাছে উত্তর খোঁজা হচ্ছে...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        
        if 'candidates' in res_json:
            bot_response = res_json['candidates'][0]['content']['parts'][0]['text']
            print(f"[+] জেমিনি উত্তর রেডি করেছে: {bot_response[:50]}...")
        else:
            print("[-] জেমিনি এপিআই এরর:", res_json)
            bot_response = "দুঃখিত, এই মুহূর্তে আমি উত্তর দিতে পারছি না।"
            
    except Exception as e:
        print("[-] কোডে সমস্যা:", e)
        bot_response = "দুঃখিত, সিস্টেমে একটু সমস্যা হচ্ছে।"

    send_message(sender_id, bot_response)

def send_message(recipient_id, text):
    print("[*] ফেসবুকে মেসেজ পাঠানোর চেষ্টা চলছে...")
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id}, 
        "message": {"text": text}
    }
    
    res = requests.post(url, json=payload)
    print("[-] ফেসবুক API রেসপন্স:", res.json())

if __name__ == "__main__":
    app.run(port=8080, debug=True)
