import re

from eventbrite import Eventbrite

from features import Base


class Users(Base):
    def check(self):
        return True

    def setup(self):
        for user in self.deployment['users']:
            if 'eventbrite' in user:
                token = self.deployment['eventbrite']['token']
                event = user['eventbrite']

                eventbrite = Eventbrite(token)
                attendees = eventbrite.get_event_attendees(event)

                for attendee in attendees['attendees']:
                    if 'password_type' not in user:
                        user['password_type'] = 'username'

                    if 'password' not in user:
                        user['password'] = attendee['profile']['email']

                    passwd = self.get_password(attendee['profile']['email'], user['password_type'], user['password'], '')

                    project = self.generate_user(attendee['profile']['email'], passwd)

                    if 'execute' in user:
                        self.execute_for_user(project, user['execute'])

            elif 'generic' in user and user['generic']:
                for x in range(user['min'], user['max']):
                    if 'password_type' not in user:
                        user['password_type'] = 'username'

                    if 'password' not in user:
                        user['password'] = ''

                    username = user['username'] + str(x)
                    password = self.get_password(username, user['password_type'], user['password'], str(x))

                    project = self.generate_user(username, password)

                    if 'execute' in user:
                        self.execute_for_user(project, user['execute'])

            else:
                username = user['username']
                project = self.generate_user(username, user['password'])

                if 'admin' in user and user['admin']:
                    self.execute("master", "oc adm policy add-cluster-role-to-user cluster-admin " + username)

                if 'sudoer' in user and user['sudoer']:
                    self.execute("master", "oc adm policy add-cluster-role-to-user sudoer " + username)

                if 'execute' in user:
                    self.execute_for_user(project, user['execute'])

        if 'execute' in self.deployment.data:
            for cmd in self.deployment['execute']:
                self.execute("master", cmd)

        if 'docker' in self.deployment.data and 'prime' in self.deployment['docker']:
            for image in self.deployment['docker']['prime']:
                self.execute("*", "docker pull " + image, True)

    def generate_user(self, username, password):
        project = re.sub(r'[^-0-9a-z]', '-', username)

        self.logger.info("Generating user %s with password %s and project %s", username, password, project)

        self.execute("master", "htpasswd -b /etc/origin/master/htpasswd " + username + " " + password, True)
        self.execute("master", "oc adm new-project " + project, False)
        self.execute("master", "oc adm policy add-role-to-user admin " + username + " -n " + project)

        return project

    def execute_for_user(self, project, execute):
        for cmd in execute:
            self.execute("master", cmd + " -n " + project)

    def get_password(self, user, type, password, index):
        if 'fixed' == type:
            return password

        if 'index' == type:
            return user + index

        if 'username' == type:
            return user

        return 'openshift'
