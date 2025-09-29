import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Informations de connexion
smtp_server = "smtp-canadarecruit.alwaysdata.net"
smtp_port = 587  # 465 si tu veux SSL
username = "canadarecruit@alwaysdata.net"
password = "Alodeme@2106"

# Expéditeur et destinataire
sender_email = username
receiver_email = "canadarecruit.00@gmail.com"

# Contenu du mail
subject = "Test envoi automatique AlwaysData"
body = "Bonjour, ceci est un test d'envoi automatique via AlwaysData."

# Préparer le message
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

try:
    # Connexion au serveur SMTP
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Sécurise la connexion
        server.login(username, password)
        server.send_message(message)
    print("✅ E-mail envoyé avec succès via AlwaysData !")
except Exception as e:
    print(f"❌ Erreur : {e}")
