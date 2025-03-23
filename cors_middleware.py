from flask import make_response, request

def add_cors_headers(response):
    print(f"Adding CORS headers to response with status code: {response.status_code}")
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, X-Requested-With, Origin, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    print(f"CORS headers added: {dict(response.headers)}")
    return response

def setup_cors_middleware(app):
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    return app
    @app.after_request
    def after_request(response):
        print(f"\n=== After Request Processing ===\nRequest Method: {request.method}\nEndpoint: {request.endpoint}\nMIME Type: {response.mimetype}")
        # Don't add CORS headers for static file responses
        if not response.mimetype.startswith('text/html'):
            print("Adding CORS headers to non-HTML response")
            return add_cors_headers(response)
        print("Skipping CORS headers for HTML response")
        return response

    @app.before_request
    def handle_preflight():
        print(f"\n=== Before Request Processing ===\nRequest Method: {request.method}\nHeaders: {dict(request.headers)}\nEndpoint: {request.endpoint}")
        if request.method == 'OPTIONS':
            print("Handling OPTIONS preflight request")
            response = make_response()
            add_cors_headers(response)
            return response

    @app.errorhandler(500)
    def handle_500_error(error):
        response = make_response({'error': 'Internal Server Error'}, 500)
        return add_cors_headers(response)

    @app.errorhandler(405)
    def handle_405_error(error):
        response = make_response({'error': 'Method Not Allowed'}, 405)
        return add_cors_headers(response)

    @app.errorhandler(404)
    def handle_404_error(error):
        response = make_response({'error': 'Not Found'}, 404)
        return add_cors_headers(response)