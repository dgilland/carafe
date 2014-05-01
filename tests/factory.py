
from collections import defaultdict

from . import core


def create_app(package_name, config=None, options=None, **flask_options):
    if options is None:
        options = {}

    app = core.FlaskCarafe(package_name, **flask_options)

    app.config.from_object(config)

    # use default dict for convenience since each key represents keyword args to init_app() functions
    opts = defaultdict(dict)
    opts.update(options)

    core.session.init_app(app)
    core.auth.init_app(app, **opts['auth'])
    core.cache.init_app(app)
    core.logger.init_app(app)

    return app
