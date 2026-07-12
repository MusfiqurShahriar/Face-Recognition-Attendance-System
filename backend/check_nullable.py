from database import CameraCommand
from sqlalchemy import inspect

for col in CameraCommand.__table__.columns:
    print(col.name, "nullable=", col.nullable)
