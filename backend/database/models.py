from datetime import date

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Date, DateTime, SmallInteger
from sqlalchemy.orm import relationship
from database.db import Base

class Department(Base):
    __tablename__ = "departments_table"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String, nullable=False)
    description = Column(Text)

    positions = relationship("Position", back_populates="department")
    employees = relationship("Employee", back_populates="department")


class Position(Base):
    __tablename__ = "positions_table"

    id = Column(Integer, primary_key=True, index=True)
    position = Column(String, nullable=False)
    description = Column(Text)
    department_id = Column(Integer, ForeignKey("departments_table.id"), nullable=False)

    department = relationship("Department", back_populates="positions")
    employees = relationship("Employee", back_populates="position")


class Zone(Base):
    __tablename__ = "zones_table"

    id = Column(Integer, primary_key=True, index=True)
    zone_name = Column(String, nullable=False)
    security_level = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime, nullable=False)

    entrances = relationship("Entrance", back_populates="zone")


class Employee(Base):
    __tablename__ = "employees_table"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    passport = Column(String, unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments_table.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions_table.id"))
    post = Column(String, nullable=False)
    badge_id = Column(Integer, nullable=False)
    security_level = Column(SmallInteger, nullable=False)
    phone_number = Column(String)
    mail = Column(String)
    address = Column(String, nullable=False)
    birth = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=False)

    department = relationship("Department", back_populates="employees")
    position = relationship("Position", back_populates="employees")
    entrances = relationship("Entrance", back_populates="employee")
    biometric = relationship("Biometric", back_populates="employee")


class Entrance(Base):
    __tablename__ = "entrances_table"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees_table.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones_table.id"), nullable=False)
    access = Column(Boolean, nullable=False)
    entrance_time = Column(DateTime(timezone=True), nullable=False)

    employee = relationship("Employee", back_populates="entrances")
    zone = relationship("Zone", back_populates="entrances")

class Biometric(Base):
    __tablename__ = "biometrics_table"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, 
        ForeignKey("employees_table.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    photo_path = Column(String, nullable=False)
    created_at = Column(Date, nullable=False, default=date.today)

    employee = relationship("Employee", back_populates="biometric")