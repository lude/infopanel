from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('redditnews', '/redditnews')
    config.add_route('forecastio', '/forecastio')
    config.add_route('twitter', '/twitter')
    config.add_route('pathtrain', '/pathtrain')
    config.add_route('greeting', '/greeting')
    config.add_route('clock', '/clock')
    config.scan()
    return config.make_wsgi_app()
