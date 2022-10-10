import logging
import json
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    return func.HttpResponse(
        json.dumps(
            {
                "print_statement": "Hello World!",
                "method": req.method,
                "url": req.url,
                "headers": dict(req.headers),
                "params": dict(req.params),
                "get_body": req.get_body().decode(),
            }
        )
    )
