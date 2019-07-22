# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client


# Your Account Sid and Auth Token from twilio.com/console
# DANGER! This is insecure. See http://twil.io/secure
account_sid = 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
auth_token = 'your_auth_token'
# client = Client(account_sid, auth_token)

def get_client(account_sid, auth_token):
    return Client(account_sid, auth_token)

def send_alert(client=None,body="Default:Found a Deer in backyard",to='+16174125569',from_='+15853265918'):
    message = client.messages \
                    .create(
                        body=body,
                        from_=from_,
                        to=to,
                    )
    print(message.sid)