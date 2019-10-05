"""
A flask server to handle webhooks from Typeform.
"""

from flask import Flask, render_template, flash, request
import logging
from pprint import pprint
from client506 import create_client
from ses import send_simple_email
from pydiscourse.exceptions import (
    DiscourseClientError
)

recipients = ['markschmucker@yahoo.com',]

logger = logging.getLogger('forms_webhook')
file_handler = logging.FileHandler('forms_webhook.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

logger.info('running web hook server.py')

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d4jjf2b6176a'


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class RequestHandler:
    def __init__(self, data):
        self.client = create_client(1)
        self.data = data
        self.answers = self.data['form_response']['answers']
        self.username = self.data['form_response']['hidden']['username']
        pprint(self.data)

    def user_is_in_group(self, group_name, username):
        members = self.client.members_of_group(group_name)
        membernames = [x['username'] for x in members]
        return username in membernames

    def add_to_group(self, group_name, username):
        group = self.client.my_group(group_name)
        self.client.add_group_members(group['id'], [username, ])


class GroupAccessHandler(RequestHandler):
    def __init__(self, data):
        RequestHandler.__init__(self, data)
        self.group_name = ''

    def process(self):
        ok = self.answers[0]['boolean']
        if ok:
            group_name = self.group_name
            if not self.user_is_in_group(group_name, self.username):
                try:
                    self.add_to_group(group_name, self.username)
                    subject = 'User was added to %s' % group_name
                    s = '%s was added to the group %s because they self-certified.' % (self.username, group_name)
                except DiscourseClientError, exc:
                    subject = 'User could not be added to %s' % group_name
                    s = '%s could not be added to the group %s. Maybe they are already a member?' % (self.username, group_name)

                s += '<br>'
                url = 'https://forum.506investorgroup.com/g/%s' % group_name
                s += 'To change this, visit the %s group settings at ' % group_name
                s += url
                s += '.'
                for recipient in recipients:
                    send_simple_email(recipient, subject, s)
                    print 'sent email'
            else:
                print 'username is already in group'


# TODO- deprecate these once the general handler is working. Will also need
# to edit the typeforms.

class QualifiedHandler(GroupAccessHandler):
    def __init__(self, data):
        GroupAccessHandler.__init__(self, data)
        self.group_name = 'QualifiedPurchasers'

class ParabellumHandler(GroupAccessHandler):
    def __init__(self, data):
        GroupAccessHandler.__init__(self, data)
        self.group_name = 'Parabellum'

class PraxisHandler(GroupAccessHandler):
    def __init__(self, data):
        GroupAccessHandler.__init__(self, data)
        self.group_name = 'Praxis'



@app.route('/qualified', methods=['GET', 'POST'])
def qualified():
    if request.method == 'POST':
        data = request.json
        q = QualifiedHandler(data)
        q.process()
        return '', 200
    else:
        return '', 400


@app.route('/parabellum', methods=['GET', 'POST'])
def parabellum():
    if request.method == 'POST':
        data = request.json
        q = ParabellumHandler(data)
        q.process()
        return '', 200
    else:
        return '', 400

@app.route('/praxis', methods=['GET', 'POST'])
def praxis():
    if request.method == 'POST':
        data = request.json
        q = PraxisHandler(data)
        q.process()
        return '', 200
    else:
        return '', 400


@app.route('/<groupname>', methods=['GET', 'POST'])
def handler(groupname):
    if request.method == 'POST':
        data = request.json
        q = GroupAccessHandler(data)
        q.group_name = groupname
        q.process()
        return '', 200
    else:
        return '', 400



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082, debug=True, threaded=True)
