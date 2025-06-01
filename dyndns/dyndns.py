#!/usr/bin/env python3

import datetime
import os
import sys

# Configuration
DOMAIN = 'hajnalmt.hu'
RECORD_NAME = 'vpn'
TOKEN_PATH = '/home/hajnalmt/digitalocean-token.txt'

def log(message):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")

def get_api_token():
    try:
        with open(TOKEN_PATH, 'r') as file:
            return file.read().strip()
    except Exception as e:
        log(f"Failed to read API token: {e}")
        sys.exit(1)

def get_current_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=10).text.strip()
    except requests.RequestException as e:
        log(f"Failed to get public IP: {e}")
        sys.exit(1)

def get_dns_record(api_token):
    url = f'https://api.digitalocean.com/v2/domains/{DOMAIN}/records'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_token}',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        records = response.json()['domain_records']
        for record in records:
            if record['type'] == 'A' and record['name'] == RECORD_NAME:
                return record
        return None
    except requests.RequestException as e:
        log(f"Failed to fetch DNS record: {e}")
        sys.exit(1)

def update_dns_record(api_token, ip, record_id=None):
    url = f'https://api.digitalocean.com/v2/domains/{DOMAIN}/records'
    if record_id:
        url += f'/{record_id}'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_token}',
    }

    data = {
        'type': 'A',
        'name': RECORD_NAME,
        'data': ip,
        'ttl': 300,
    }

    try:
        if record_id:
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log(f"Failed to update DNS record: {e}")
        sys.exit(1)

# --- Main logic ---
if __name__ == "__main__":
    API_TOKEN = get_api_token()
    ipv4 = get_current_public_ip()
    log(f"Current public IPv4: {ipv4}")

    current_record = get_dns_record(API_TOKEN)
    if current_record:
        if current_record['data'] != ipv4:
            resp = update_dns_record(API_TOKEN, ipv4, current_record['id'])
            log(f"DNS updated: {resp}")
        else:
            log("IP has not changed. No update needed.")
    else:
        resp = update_dns_record(API_TOKEN, ipv4)
        log(f"No existing record found. Created new DNS record: {resp}")
