import mysql.connector
from datetime import date
import smtplib
from email.message import EmailMessage
import os

# Ler variáveis de ambiente definidas no GitHub Actions
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Conectar ao MySQL
db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)
cursor = db.cursor(dictionary=True)

# Buscar alimentos que ainda não receberam alerta
cursor.execute("SELECT * FROM products WHERE alert_sent = 0")
foods = cursor.fetchall()

today = date.today()

# Configurar servidor SMTP do Gmail
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(EMAIL_USER, EMAIL_PASS)

for food in foods:
    expiry_date = food['expiry']
    diff_days = (expiry_date - today).days

    if 0 < diff_days <= 60 and food.get('user_email'):
        msg = EmailMessage()
        msg['Subject'] = f"Alerta: {food['name']} perto da validade"
        msg['From'] = EMAIL_USER
        msg['To'] = food['user_email']
        msg.set_content(f"O alimento '{food['name']}' vence em {diff_days} dias.")

        try:
            server.send_message(msg)
            print(f"Email enviado para {food['user_email']} sobre '{food['name']}'")

            cursor.execute("UPDATE products SET alert_sent = 1 WHERE id = %s", (food['id'],))
            db.commit()
        except Exception as e:
            print(f"Falha ao enviar email para {food['user_email']}: {e}")

server.quit()
cursor.close()
db.close()
