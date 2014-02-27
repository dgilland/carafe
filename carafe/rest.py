
from werkzeug.exceptions import BadRequest

class RestCtrl(object):
    __model__ = None

    # add +1 to max limit so that consumers can query for an extra record to determine if more records exist
    # @todo: may want to expand return to include
    DEFAULT_LIMIT = 51
    MAX_LIMIT = 101
    DEFAULT_SEARCH_KEY = 'q'

    def __init__(self, db, config=None):
        self.db = db
        self.config = config

    @property
    def Model(self):
        '''Proxy to REST model'''
        return self.__model__

    @property
    def query(self):
        '''Proxy to REST model's query property'''
        return self.Model.query

    def index(self, params=None, max_limit=True, as_list=True):
        '''Return list of models matching search parameters.'''
        params = params or {}
        limit = self.get_limit(params.get('limit'), max_limit=max_limit)
        offset = self.get_offset(params.get('offset'))

        results = self.search(self.query, params, limit, offset)

        if as_list:
            results = results.all()

        return results

    def search(self, query, search_dict=None, limit=None, offset=None):
        '''Apply `search()` to given `query`'''
        search_string = (search_dict or {}).get(self.DEFAULT_SEARCH_KEY)
        return query.search(search_string, search_dict, limit=limit, offset=offset)

    def get_limit(self, limit, default_limit=True, max_limit=True):
        '''Get acceptable limit by obeying default and max.'''
        default_limit = self.DEFAULT_LIMIT if default_limit is True else default_limit
        # allow exception here since caller should not pass in an invalid max
        max_limit = int(self.MAX_LIMIT if max_limit is True else max_limit)

        try:
            limit = min(int(limit), max_limit)
        except Exception:
            limit = default_limit

        return limit

    def get_offset(self, offset, default_offset=0):
        '''Get acceptable offset.'''
        try:
            offset = int(offset)
        except Exception:
            offset = default_offset

        return offset

    def get(self, _id):
        '''Get single record by id.'''
        return self.Model.get(_id)

    def post(self, data, strict=True, commit=True):
        '''Create new record. Optionally commit to database.'''
        model = self.Model(strict=strict, **data)
        self.add(model, commit=commit)
        return model

    def put(self, _id, data, strict=True, commit=True):
        '''Update existing record. Optionally commit to database.'''
        # @note: intentionally not doing an update query (e.g. query(..).get(..).update({}))
        # since there may be sqlalchemy attribute events that need to execute
        model = self.Model.get(_id)
        if model:
            model.update(data, strict=strict)
            self.add(model, commit=commit)
        return model

    def patch(self, _id, data, strict=True, commit=True):
        '''Update existing record (same as `put()`. Optionally commit to database.'''
        return self.put(_id, data, strict=strict, commit=commit)

    def delete(self, _id, commit=True):
        '''Delete record. Returns True if rows deleted else False.'''
        # use filter_by() so we can call delete() (i.e. delete() doesn't work if you use get(_id))
        deleted = self.query.filter_by(_id=_id).lazyload('*').delete()
        if commit:
            self.commit()
        return bool(deleted)

    def add(self, obj, commit=False):
        '''Add obj to session and optionally commit.'''
        self.db.session.add(obj)
        if commit:
            self.commit()

    def commit(self):
        '''Try to commit session. Raise HTTPException if commit fails.'''
        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()
            # re-raise as subclassed HTTPException
            raise BadRequest(str(e))

