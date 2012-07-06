from london.apps.sessions.base import BaseSession
from london.apps.sessions.models import Session
from london.exceptions import ObjectDoesNotExist

class SessionStore(BaseSession):
    def load(self):
        try:
            self._values = Session.query().get(pk=self.key)
        except (TypeError, ObjectDoesNotExist):
            self.create()

    def create(self):
        self._values = Session()
        self._values.save()
        self.key = self._values.pk

    def save(self):
        self._values.save()

