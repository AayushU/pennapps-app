from twilio.rest import TwilioRestClient

account_sid = ""
auth_token = ""
client = TwilioRestClient(account_sid, auth_token)

message = client.sms.messages.create(to="1234345", from="23432423423", body="hi thurr")

