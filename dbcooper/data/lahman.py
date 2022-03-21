descriptions = {
    "Salaries": {
        "schema": "Player salaries, going back to 1985.",
        "columns": {
            "yearID": "Year.",
            "teamID": "Team ID.",
            "lgID": "League ID.",
            "playerID": 'Player ID. See e.g. the "People" table for player info.',
            "Salary": "Salary (in dollars).",
        }
    }
}

def lahman_sqlite(engine=None, schema="lahman"):
    from sqlalchemy import create_engine
    if engine is None:
        NotImplementedError()
        #engine = create_engine("sqlite://")

    engine.execute("ATTACH ':memory:' AS %s" % schema)
    load_tables_for_engine(engine, schema=schema)
    #return engine

def load_tables_for_engine(engine, exclude=[], **kwargs):
    import lahman
    for name in lahman._accessors:
        if name in exclude: continue
        df = getattr(lahman, name)()
        df.to_sql(name, engine, **kwargs)

