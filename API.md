# Documentation

## Health Check
- **URL**: /health
- **METHOD**: `GET`
- **MIMETYPE**: application/json
- **PARAMS**: N/A
- **SUCCESS RESPONSE**:
    - *STATUS*: 200 OK
    - *BODY*: `{"success": True, "message": "Completed Health Check", "data": { "status": "PASS", "info": "All services are online"}}`
- **ERROR RESPONSE**:
    - *STATUS*: 200 OK
    - *BODY*: `{"success": False, "message": "Completed Health Check", "data": {"status": "FAIL", "info": "At least one service is offline"}}`
- **SAMPLE CALL** (using [httipe](https://httpie.io/)): `http GET localhost/health`

## Word Count
- **URL**: /word-count
- **METHOD**: `GET` | `POST`
- **MIMETYPE**: application/json
- **PARAMS**:
    - `GET`:
        - **job_id**|string|required : returned in response returned from `POST /word-count`
    - `POST`
        - **url**|string|required : url of website to scrape / count words of
- **SUCCESS RESPONSE**:
    - `GET`
        - *STATUS*: 200 OK
        - *BODY*: `{"success": True, "message": "Fetched Job: 507f1f77bcf86cd799439011", "data": { "_id": "507f1f77bcf86cd799439011", "url": "http://example.com", "status": "COMPLETE", "word_count": {"hello": 1, ...}}}`
    - `POST`
        - *STATUS*: 202 ACCEPTED
        - *BODY*: `{"success": True, "message": "Scheduled Job: 507f1f77bcf86cd799439011", "data": { "_id": "507f1f77bcf86cd799439011", "url": "http://example.com", "status": "IN_PROGRESS"}}`
- **ERROR RESPONSE**:
    - `GET`
        - *STATUS*: 400 BAD REQUEST
        - *BODY*: `{"success": False, "message": "You must provdie a valid 'job_id' in your GET request JSON", "data": {}}`

    OR

        - *STATUS*: 400 BAD REQUEST
        - *BODY*: `{"success": False, "message": "Please make requests using the application/json MIME type", "data": {}}`

    OR

        - *STATUS*: 500 SERVER ERROR
        - *BODY*: `{"success": False, "message": "Oh dear! Something unexpected occurred..", "data": {}}`
    - `POST`
        - *STATUS*: 400 BAD REQUEST
        - *BODY*: `{"success": False, "message": "You must provdie a valid 'url' in your GET request JSON", "data": {}}`

    OR

        - *STATUS*: 400 BAD REQUEST
        - *BODY*: `{"success": False, "message": "Please make requests using the application/json MIME type", "data": {}}`

    OR

        - *STATUS*: 500 SERVER ERROR
        - *BODY*: `{"success": False, "message": "Oh dear! Something unexpected occurred..", "data": {}}`
- **SAMPLE CALL** (using [httipe](https://httpie.io/)):
    - `http POST localhost/word-count <<< '{"url": "https://www.gutenberg.org/files/42525/42525-h/42525-h.htm"}'`
    - `http GET localhost/word-count <<< '{"job_id": "62607a5aa4d78daf9df91565"}`
