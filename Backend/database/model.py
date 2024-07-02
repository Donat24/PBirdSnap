import datetime
import enum
import uuid
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    UUID,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class BirdSnapLike(Base):
    __tablename__ = "birdsnaplike"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    birdsnap_id: Mapped[int] = mapped_column(ForeignKey("birdsnap.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    like_time: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"BirdSnapLike(id={self.id}, birdsnap_id={self.birdsnap_id}, user_id={self.user_id}, like_time={self.like_time})"

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    password_hash: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    creation_time: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    devices: Mapped[List["Device"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    likes: Mapped[List["BirdSnap"]] = relationship(
        back_populates="users_liked",
        secondary=BirdSnapLike.__table__,
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, name={self.name}, email={self.email})"

class DeviceType(str, enum.Enum):
    TEST_DEVICE = "TEST_DEVICE"
    PI_ZERO = "PI_ZERO"

class Device(Base):
    __tablename__ = "device"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    type: Mapped[DeviceType] = mapped_column(Enum(DeviceType))
    name: Mapped[str] = mapped_column(String)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    owner: Mapped["User"] = relationship(
        back_populates="devices",
        lazy="selectin"
    )

    is_info_public: Mapped[bool] = mapped_column(Boolean, default=True)
    longitude:Mapped[Optional[float]] = mapped_column(Float)
    latitude:Mapped[Optional[float]] = mapped_column(Float)
    
    public_by_default: Mapped[bool] = mapped_column(Boolean, default=True)
    birdsnaps: Mapped[List["BirdSnap"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Device(id={self.id}, name={self.name}, owner_id={self.owner_id}, public_by_default={self.public_by_default})"


class BirdSnapImage(Base):
    __tablename__ = "birdsnapimage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    birdsnap_id: Mapped[int] = mapped_column(ForeignKey("birdsnap.id"))
    birdsnap: Mapped["BirdSnap"] = relationship(
        back_populates="images",
        lazy="selectin"
    )
    path: Mapped[str] = mapped_column(String)

    def __repr__(self) -> str:
        return f"BirdSnapImage(id={self.id}, birdsnap_id={self.birdsnap_id}, path={self.path})"

class BirdSnapStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    AVAILABLE = "AVAILABLE"
    NOBIRD = "NOBIRD"
    DELETED = "DELETED"


class BirdSnap(Base):
    __tablename__ = "birdsnap"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[BirdSnapStatus] = mapped_column(
        Enum(BirdSnapStatus),
        server_default=BirdSnapStatus.PROCESSING,
    )
    is_public: Mapped[bool] = mapped_column(Boolean)
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    device: Mapped["Device"] = relationship(
        back_populates="birdsnaps",
        lazy="selectin"
    )
    snap_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    images: Mapped[List["BirdSnapImage"]] = relationship(
        back_populates="birdsnap",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    users_liked: Mapped[List["User"]] = relationship(
        back_populates="likes",
        secondary=BirdSnapLike.__table__,
        lazy="selectin"
    )
    bird_species: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )

    @hybrid_property
    def device_owner(self) -> User:
        return self.device.owner

    def __repr__(self) -> str:
        return f"Device(id={self.id}, is_public={self.is_public}, device_id={self.device_id}, snap_time={self.snap_time}, bird_species={self.bird_species})"
