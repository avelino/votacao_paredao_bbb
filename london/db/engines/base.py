class DatabaseEngine(object):
    def __init__(self):
        pass

    def is_open(self):
        raise NotImplementedError('Method "is_open" not implemented')

    def execute_query(self, query):
        raise NotImplementedError('Method "execute_query" not implemented')

    def create_database(self):
        raise NotImplementedError('Method "create_database" not implemented')

    def drop_database(self):
        raise NotImplementedError('Method "drop_database" not implemented')

    # Multi database routing methods --------

    def allow_read(self, model, **kwargs):
        return True

    def allow_write(self, model, action, instance=None, query=None):
        return True

    def allow_relation(self, obj1, obj2):
        # TODO: this is not working yet
        return True

    def allow_syncdb(self, model):
        # TODO: this is not working yet
        return True

    def allow_prepare_indexes(self, model):
        return True

