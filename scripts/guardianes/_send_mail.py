#!/usr/bin/env python3
import sys, ssl, smtplib, argparse, os
cfg={}
with open(os.path.expanduser('~/.smtp_creds')) as f:
    for line in f:
        line=line.strip()
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1); cfg[k]=v
from email.message import EmailMessage
ap=argparse.ArgumentParser()
ap.add_argument('--to',required=True)
ap.add_argument('--subject',required=True)
ap.add_argument('--body',required=True)
a=ap.parse_args()
msg=EmailMessage()
msg['From']=cfg['SMTP_FROM']; msg['To']=a.to; msg['Subject']=a.subject
msg.set_content(a.body)
ctx=ssl.create_default_context()
with smtplib.SMTP_SSL(cfg['SMTP_HOST'], int(cfg['SMTP_PORT']), context=ctx, timeout=30) as s:
    s.login(cfg['SMTP_USER'], cfg['SMTP_PASS'])
    s.send_message(msg)
print('OK enviado a', a.to)
