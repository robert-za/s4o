import os

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.params import Query
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.logger import logger
from app.schemas.geolocation import GeolocationValidator, IpOrAddressValidator
from app.services.geolocation_service import GeolocationService

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)


API_RATE_LIMIT_PER_DAY = os.getenv("API_RATE_LIMIT_PER_DAY")


@app.get("/geolocation")
@limiter.limit(f"{API_RATE_LIMIT_PER_DAY}/day")
def get_geolocation(
    request: Request, query: IpOrAddressValidator = Depends(), db_session: Session = Depends(get_db)
) -> JSONResponse:
    try:
        resp = GeolocationService.fetch_from_local_database(query.address, db_session)
        if resp:
            return JSONResponse(content={"data": resp}, status_code=status.HTTP_200_OK)

        remote_resp = GeolocationService.fetch_from_remote_service(query.address)
        validated_data = GeolocationService.validate_data(remote_resp, query.address)
        serialized_data = GeolocationService.save_remote_data_in_local_database(validated_data, db_session)
        return JSONResponse(
            content={"data": [serialized_data.model_dump() if serialized_data else None]},
            status_code=status.HTTP_200_OK,
        )

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": str(e)})
    except Exception as e:
        logger.error(f"Error processing geolocation query for {str(query.address)}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"error": "Something went wrong. Please contact support."}
        )


@app.post("/geolocation")
@limiter.limit(f"{API_RATE_LIMIT_PER_DAY}/day")
def post_geolocation(
    request: Request, data: GeolocationValidator, db_session: Session = Depends(get_db)
) -> JSONResponse:
    if not data.ip:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"error": "Only IP addresses are allowed."}
        )

    if GeolocationService.fetch_from_local_database(data.ip, db_session):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": "Address already stored in the database."}
        )

    validated_data = GeolocationService.validate_data(data.model_dump(), data.ip)

    try:
        _ = GeolocationService.save_remote_data_in_local_database(validated_data, db_session)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "All good 🫡."})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": str(e)})


@app.delete("/geolocation")
@limiter.limit(f"{API_RATE_LIMIT_PER_DAY}/day")
def delete_geolocation(
    request: Request,
    query: IpOrAddressValidator = Query(...),  # type: ignore[assignment]
    db_session: Session = Depends(get_db),
) -> JSONResponse:
    try:
        db_entries_deleted = GeolocationService.delete(query.address, db_session)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"{db_entries_deleted} geolocation object(s) deleted successfully."},
        )
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": str(e)})
    except Exception as e:
        logger.error(f"Error processing geolocation query for {str(query.address)}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"error": "Something went wrong. Please contact support."}
        )


# for docker compose debugging
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
