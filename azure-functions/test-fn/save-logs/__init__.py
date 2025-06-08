import logging
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        # Simple test response
        return func.HttpResponse(
            "Hello! Function is working correctly.",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
