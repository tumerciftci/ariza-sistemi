# PROFESYONEL WEB ARIZA TAKİP SİSTEMİ (PERSONEL GRAFİĞİ DAHİL)

from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import io
from reportlab.pdfgen import canvas
from datetime import datetime
from collections import Counter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ariza.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MODELLER
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))

class Ariza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tarih = db.Column(db.String(50))
    cihaz = db.Column(db.String(100))
    aciklama = db.Column(db.String(200))
    durum = db.Column(db.String(50))
    personel = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# LOGIN
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/dashboard')
    return render_template('login.html')

# DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():
    arizalar = Ariza.query.all()

    acik = Ariza.query.filter_by(durum="Açık").count()
    kapali = Ariza.query.filter_by(durum="Kapalı").count()

    # PERSONEL ANALİZ
    personel_list = [a.personel for a in arizalar if a.personel]
    sayim = Counter(personel_list)

    personel_isimler = list(sayim.keys())
    personel_sayilar = list(sayim.values())

    return render_template(
        'dashboard.html',
        arizalar=arizalar,
        acik=acik,
        kapali=kapali,
        personel_isimler=personel_isimler,
        personel_sayilar=personel_sayilar
    )

# EKLE
@app.route('/ekle', methods=['GET','POST'])
@login_required
def ekle():
    if request.method == 'POST':
        yeni = Ariza(
            tarih=datetime.now().strftime("%Y-%m-%d %H:%M"),
            cihaz=request.form['cihaz'],
            aciklama=request.form['aciklama'],
            durum="Açık",
            personel=request.form['personel']
        )
        db.session.add(yeni)
        db.session.commit()
        return redirect('/dashboard')
    return render_template('ekle.html')

# KAPAT
@app.route('/kapat/<int:id>')
@login_required
def kapat(id):
    ariza = Ariza.query.get(id)
    ariza.durum = "Kapalı"
    db.session.commit()
    return redirect('/dashboard')

# PDF
@app.route('/pdf')
@login_required
def pdf():
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    y = 800
    for a in Ariza.query.all():
        p.drawString(50, y, f"{a.cihaz} - {a.durum}")
        y -= 20

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="rapor.pdf")

# LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# BAŞLAT
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password=generate_password_hash('1234')))
            db.session.commit()

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ==============================
# templates/dashboard.html (PERSONEL GRAFİĞİ EKLENDİ)
# ==============================

"""
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<h4>Personel Performansı</h4>
<canvas id="personelChart"></canvas>

<script>
new Chart(document.getElementById('personelChart'), {
    type: 'bar',
    data: {
        labels: {{ personel_isimler|tojson }},
        datasets: [{
            label: 'Çözülen Arıza',
            data: {{ personel_sayilar|tojson }}
        }]
    }
});
</script>
"""
