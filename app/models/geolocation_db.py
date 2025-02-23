from typing import Any, Dict, Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GeolocationDB(Base):
    __tablename__ = "geolocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(String(50), index=True)
    address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None, index=True)
    continent_code: Mapped[str]
    continent_name: Mapped[str]
    country_code: Mapped[str]
    country_name: Mapped[str]
    region_code: Mapped[str]
    region_name: Mapped[str]
    city: Mapped[str]
    zip: Mapped[str]
    latitude: Mapped[float]
    longitude: Mapped[float]

    def as_dict(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != "id"}
