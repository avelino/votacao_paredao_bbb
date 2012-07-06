from london.utils.imports import import_anything

def get_service(settings, name):
    """
    Finds the service dictionary in settings and returns a service instance.
    """
    service_dict = settings.SERVICES[name].copy()
    service_class = import_anything(service_dict.pop('handler'))
    service_inst = service_class(**service_dict)
    service_inst.name = name
    return service_inst

def get_server(path, service):
    """
    Finds the server by path and returnst the instance for the given service
    """
    service_class = import_anything(path)
    return service_class(service)

