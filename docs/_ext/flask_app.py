def setup(sphinx):
    from invenio.base.factory import create_app
    app = create_app()
    ctx = app.test_request_context('/')
    ctx.push()
