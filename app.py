import os
import urllib
from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash
from flask_oauthlib.client import OAuth
import json


app = Flask(__name__)
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

github = oauth.remote_app(
    'github',
    consumer_key='CONSUMER_KEY', #get from github
    consumer_secret='CONSUMER_SECRET,
    request_token_params={'scope': 'user:email,user:follow,notifications'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    
)


@app.route('/', methods=['POST', 'GET'])
def index():
    flash("Please be patient. You may experience slow loading.")
    return render_template('index.html')


@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True))


@app.route('/logout')
def logout():
    session.pop('github_token', None)
    return redirect(url_for('index'))


@app.route('/home')
def authorized():
    resp = github.authorized_response()

    try:
        resp['access_token']
    except KeyError:
        return redirect(url_for('login'))

    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )



    session['github_token'] = (resp['access_token'], '')

    me = github.get('user')
    user_data = json.dumps((me.data))

    parsed_data = json.loads(user_data)
    print(parsed_data)
    events_data = json.load(urllib.urlopen(parsed_data["received_events_url"]))

    
    final_data = []

    count = 0
    for obj in events_data:
        count += 1

    for i in range(0, count):
        user_name = events_data[i]["actor"]["login"]
        user_image = events_data[i]['actor']["avatar_url"]
        target_repo = events_data[i]['repo']['name']
        date = events_data[i]["created_at"]
        id = events_data[i]["id"]

        if events_data[i]["type"] == "WatchEvent":
            action = "starred " #github thinks watch means star -___-
        if events_data[i]["type"] == "CreateEvent":
            action = "created "
        if events_data[i]["type"] == "ForkEvent":
            action = "forked "    
        
        final_data.append({
            'name': user_name,
            'avatar': user_image,
            'target': target_repo,
            'action':action,
            'date':date,
            'id':id,
            'type':events_data[i]["type"]
        })
    return render_template("home.html", data=final_data)


@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
