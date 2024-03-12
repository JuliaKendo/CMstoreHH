def init():
    global use_sqlite
    global redis_conn
    global sqlite_conn
    
    use_sqlite = False
    redis_conn = None
    sqlite_conn = None
