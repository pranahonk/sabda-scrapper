def create_response(status="success", message="", data=None, metadata=None):
    """Create standardized API response"""
    response = {
        "status": status,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    if metadata is not None:
        response["metadata"] = metadata
    
    return response
