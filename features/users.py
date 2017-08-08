import re

from eventbrite import Eventbrite

from features import Base


class Users(Base):
    def check(self):
        return True

    def applicable(self):
        return ["master"]

    def call(self, connection):
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

                    project = self.generate_user(attendee['profile']['email'], passwd, connection)

                    if 'execute' in user:
                        self.execute_for_user(project, user['execute'], connection)

            elif 'generic' in user and user['generic']:
                for x in range(user['min'], user['max']):
                    if 'password_type' not in user:
                        user['password_type'] = 'username'

                    if 'password' not in user:
                        user['password'] = ''

                    username = user['username'] + str(x)
                    password = self.get_password(username, user['password_type'], user['password'], str(x))

                    project = self.generate_user(username, password, connection)

                    if 'execute' in user:
                        self.execute_for_user(project, user['execute'], connection)

            else:
                username = user['username']
                project = self.generate_user(username, user['password'], connection)

                if 'admin' in user and user['admin']:
                    connection.execute("oc adm policy add-cluster-role-to-user cluster-admin " + username)

                if 'sudoer' in user and user['sudoer']:
                    connection.execute("oc adm policy add-cluster-role-to-user sudoer " + username)

                if 'execute' in user:
                    self.execute_for_user(project, user['execute'], connection)

        if 'execute' in self.deployment.data:
            for cmd in self.deployment['execute']:
                connection.execute(cmd)

    def generate_user(self, username, password, connection):
        project = re.sub(r'[^-0-9a-z]', '-', username)

        self.logger.info("Generating user %s with password %s and project %s", username, password, project)

        connection.execute("htpasswd -b /etc/origin/master/htpasswd " + username + " " + password, True)
        connection.execute("oc adm new-project " + project, False)
        connection.execute("oc adm policy add-role-to-user admin " + username + " -n " + project)

        return project

    def execute_for_user(self, project, execute, connection):
        for cmd in execute:
            connection.execute(cmd + " -n " + project)

    def get_password(self, user, type, password, index):
        if 'fixed' == type:
            return password

        if 'index' == type:
            return user + index

        if 'username' == type:
            return user

        return 'openshift'
