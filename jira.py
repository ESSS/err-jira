from errbot import BotPlugin
import logging
import re
import requests


class Jira(BotPlugin):
    """A plugin for interacting with Atlassian JIRA"""
    min_err_version = '2.2.0-beta'  # Optional, but recommended
    max_err_version = '2.2.0-beta'  # Optional, but recommended

    def get_configuration_template(self):
        """Defines the configuration structure this plugin supports"""
        return {'URL': "http://jira.example.com",
                'USERNAME': 'err',
                'PASSWORD': 'secret',
                'PROJECTS': ['FOO', 'BAR']}

    def get_issue(self, issue_id):
        """Retrieves issue JSON from JIRA"""
        url = self.config['URL']
        if url.startswith('<') and url.endswith('>'):
            url = url[1:-1]
        url = url + '/rest/api/latest/issue/' + issue_id
        logging.debug('[JIRA] request: %s' % url)
        response = requests.get(url, auth=(self.config['USERNAME'], self.config['PASSWORD']))
        return response

    def callback_message(self, mess):
        """A callback which responds to mention of JIRA issues"""
        if self.config:
            matches = []
            regexes = []
            for project in self.config['PROJECTS']:
                regexes.append(r'(%s\-[0-9]+)' % project)
            for regex in regexes:
                matches.extend(re.findall(regex, mess.body, flags=re.IGNORECASE))
            if matches:
                # set() gives us uniques, but does not preserve order.
                for match in set(matches):
                    issue_id = match
                    logging.debug("[JIRA] matched issue_id: %s" % issue_id)
                    issue_response = self.get_issue(issue_id)
                    if issue_response.status_code in (200,):
                        logging.debug("[JIRA] retrieved issue data: %s" % issue_response)
                        issue_summary = issue_response.json()['fields']['summary']
                        html_message = "<html><body><a href=\"%s/browse/%s\">%s</a>: %s</body></html>" % (self.config['URL'], issue_id, issue_id, issue_summary,)
                        self.send(mess.frm, html_message, message_type=mess.type)
                    elif issue_response.status_code in (401,):
                        self.send(mess.frm, "Access Denied", message_type=mess.type)
                    elif issue_response.status_code in (404,):
                        self.send(mess.frm, "Issue not found", message_type=mess.type)
                    else:
                        logging.error("[JIRA] encountered unknown response status code: %s" % issue_response.status_code)
                        logging.error("[JIRA] response body: %s" % issue_response.json())
                        self.send(mess.frm, "Recieved an unexpected response, see logs for more detail", message_type=mess.type)
