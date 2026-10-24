import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()
cnx = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
)
cur = cnx.cursor()
cur.execute("SELECT DATABASE(), VERSION()")
print("Connected:", cur.fetchone())
cur.execute("SELECT COUNT(*) FROM Player")
print("Players:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM Matches")
print("Matches:", cur.fetchone()[0])
cur.close()
cnx.close()