#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
vCenter 8 Certificate Expiration Monitor
This script checks TLS certificate validity via REST API and sends alerts.
"""

__author__ = "Jose Antonio Vico"
__version__ = "1.0.3"
__status__ = "Production"
__license__ = "Apache License 2.0"

import requests
import urllib3
import smtplib
import re
import os
from datetime import datetime, timezone
from email.message import EmailMessage

# --- CONFIGURATION ---
VCENTERS = [
    "vcenter01.localdomain.local",
    "vcenter02.localdomain.local"
]
USER = "monitor-cert@vsphere.local"
PASSWORD = os.getenv('VC_PASS') 

# Mail Configuration
SMTP_RELAY = "smtpgw2.localdomain.local"
MAIL_SENDER = "alerts.infra@DOMAIN"
MAIL_TO = "admin.infra@DOMAIN"

# Alert Thresholds
DAYS_THRESHOLD = 10   # Start sending emails (INFO status)
ERROR_THRESHOLD = 3   # Switch to ERROR status in logs/mail

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_vc_date(date_str):
    """Cleans and parses vCenter 8 ISO 8601 date strings."""
    clean_date = re.sub(r'\.\d+Z$', 'Z', date_str)
    return datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def send_alert_mail(vcenter, msg_body, is_critical=False):
    """Sends notification via SMTP relay on port 25."""
    subject_prefix = "CRITICAL" if is_critical else "WARNING"
    msg = EmailMessage()
    msg.set_content(msg_body)
    msg['Subject'] = f"{subject_prefix}: Certificate Expiration - {vcenter}"
    msg['From'] = MAIL_SENDER
    msg['To'] = MAIL_TO
    try:
        with smtplib.SMTP(SMTP_RELAY, 25, timeout=10) as s:
            s.send_message(msg)
    except Exception as e:
        print(f"!!! Error sending email for {vcenter}: {e}")

def check_certs():
    if not PASSWORD:
        print("[ERROR] Environment variable VC_PASS is not defined.")
        return

    for vc in VCENTERS:
        status_line = ""
        short_name = vc.split('.')[0]
        log_filename = f"/var/log/vcenter_{short_name}.log"
        
        try:
            # 1. Session Login
            sess_resp = requests.post(f"https://{vc}/api/session", auth=(USER, PASSWORD), verify=False, timeout=12)
            sess_resp.raise_for_status()
            headers = {"vmware-api-session-id": sess_resp.json()}

            # 2. Query TLS Certificate
            tls_url = f"https://{vc}/api/vcenter/certificate-management/vcenter/tls"
            tls_resp = requests.get(tls_url, headers=headers, verify=False, timeout=10)
            
            if tls_resp.status_code == 403:
                status_line = f"[ERROR] Insufficient permissions (403) on {vc}"
            else:
                tls_resp.raise_for_status()
                data = tls_resp.json()
                expiry_str = data.get('valid_until') or data.get('cert_info', {}).get('valid_until')
                
                if not expiry_str:
                    status_line = f"[ERROR] Could not extract expiration date on {vc}"
                else:
                    expiry_date = parse_vc_date(expiry_str)
                    days_left = (expiry_date - datetime.now(timezone.utc)).days

                    # --- ALERTING LOGIC ---
                    if days_left < 0:
                        status_line = f"[ERROR] Certificate EXPIRED on {vc}"
                        send_alert_mail(vc, f"URGENT: Certificate on {vc} has EXPIRED.", True)
                    
                    elif days_left <= ERROR_THRESHOLD:
                        status_line = f"[ERROR] CRITICAL: {days_left} days left on {vc}"
                        send_alert_mail(vc, f"CRITICAL: Certificate on {vc} expires in {days_left} days ({expiry_date}).", True)
                    
                    elif days_left <= DAYS_THRESHOLD:
                        status_line = f"[INFO] Warning: {days_left} days left on {vc}"
                        send_alert_mail(vc, f"WARNING: Certificate on {vc} expires in {days_left} days ({expiry_date}).", False)
                    
                    else:
                        status_line = f"[INFO] Certificate OK on {vc} ({days_left} days left)"

            # 3. Session Logout
            requests.delete(f"https://{vc}/api/session", headers=headers, verify=False)

        except Exception as e:
            status_line = f"[ERROR] Connection failed to {vc}: {str(e)}"

        # 4. Log Writing
        try:
            with open(log_filename, "w") as f:
                f.write(status_line + "\n")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {vc} -> {status_line}")
        except Exception as log_err:
            print(f"!!! Could not write to log {log_filename}: {log_err}")

if __name__ == "__main__":
    check_certs()