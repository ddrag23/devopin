"""
Example of how to use the logger in different parts of the application
"""

from .logging_config import get_logger

# Example 1: In a service file
def example_service_function():
    logger = get_logger("app.service")
    logger.info("Service function called")
    logger.debug("Processing data...")
    
    try:
        # Your service logic here
        result = perform_some_operation()
        logger.info(f"Operation completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in service function: {str(e)}")
        raise

def perform_some_operation():
    return "success"

# Example 2: In an API endpoint
def example_api_endpoint():
    logger = get_logger("app.api")
    logger.info("API endpoint called")
    
    try:
        # Your API logic here
        data = {"status": "ok", "message": "API call successful"}
        logger.info("API call completed successfully")
        return data
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return {"status": "error", "message": str(e)}

# Example 3: In a background task or monitoring
def example_monitoring_task():
    logger = get_logger("app.monitoring")
    logger.info("Starting monitoring task")
    
    # Log different levels
    logger.debug("Debug information for monitoring")
    logger.info("Monitoring task running normally")
    logger.warning("Warning: threshold approaching")
    logger.error("Error: threshold exceeded")
    
    logger.info("Monitoring task completed")

# Example 4: In database operations
def example_database_operation():
    logger = get_logger("app.database")
    logger.info("Database operation started")
    
    try:
        # Your database logic here
        logger.debug("Executing database query")
        result = "database_result"
        logger.info(f"Database operation successful: {result}")
        return result
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise