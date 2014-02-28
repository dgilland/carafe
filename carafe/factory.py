
from collections import defaultdict

import core

def create_app(package_name, config=None, options=None, **flask_options):
    if options is None:
        options = {}

    app = core.FlaskCarafe(package_name, **flask_options)

    app.config.from_object(config)

    # use default dict for convenience since each key represents keyword args to init_app() functions
    opts = defaultdict(dict)
    opts.update(options)

    if app.config.get('CARAFE_JSON_ENABLED', True):
        core.json.init_app(app, **opts['json'])

    if app.config.get('CARAFE_SESSION_ENABLED', True):
        core.session.init_app(app, **opts['session'])

    if app.config.get('CARAFE_AUTH_ENABLED', True):
        core.auth.init_app(app, **opts['auth'])

    if app.config.get('CARAFE_CACHE_ENABLED', True):
        core.cache.init_app(app, **opts['cache'])

    if app.config.get('CARAFE_LOGGER_ENABLED', True):
        core.logger.init_app(app, **opts['cache'])

    return app
