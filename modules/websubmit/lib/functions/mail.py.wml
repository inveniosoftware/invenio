
import smtplib
    
def send_email(fromaddr, toaddr, body, attempt=0):
    if toaddr != "":
        if attempt > 2:
            raise functionError('error sending email to %s: SMTP error; gave up after 3 attempts' % toaddr)
        try:
            server = smtplib.SMTP('localhost')
            server.sendmail(fromaddr, toaddr, body)
            server.quit()
        except:
            time.sleep(10)
            send_email(fromaddr, toaddr, body, attempt+1)
            return
        
def forge_email(fromaddr, toaddr, bcc, subject, content):
    body = 'From: %s\nTo: %s\nbcc:%s\nContent-Type: text/plain; charset=utf-8\nSubject: %s\n%s' % (fromaddr, toaddr, bcc,subject, content)
    return body