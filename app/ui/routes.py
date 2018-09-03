from app.ui import blueprint, email
from flask import render_template
from flask_login import login_required


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')



@blueprint.route('/inbox')
@login_required
def route_email():
    emails = email.query_messages()
    return render_template('email.html', emails=emails)
