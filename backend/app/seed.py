"""Seed the database with a demo user and a sample dataset.

Run with:  python -m app.seed
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.models import (
    Dataset,
    DatasetStatus,
    SourceType,
    User,
)
from app.services import data_service, profiling_service

DEMO_EMAIL = "demo@aibi.dev"
DEMO_PASSWORD = "demo12345"
SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "sales.csv"


def seed() -> None:
    """Create tables, a demo user, and register the sample dataset."""
    configure_logging()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                full_name="Demo Analyst",
                hashed_password=hash_password(DEMO_PASSWORD),
                is_superuser=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Created demo user %s" % DEMO_EMAIL)

        existing = (
            db.query(Dataset)
            .filter(Dataset.owner_id == user.id, Dataset.name == "Sample Sales")
            .first()
        )
        if existing:
            logger.info("Sample dataset already present; skipping.")
            return

        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / "sample_sales.csv"
        shutil.copyfile(SAMPLE_CSV, dest)

        df = data_service.load_dataframe(str(dest), "csv")
        cleaned, _ = data_service.clean_dataframe(df)
        dataset = Dataset(
            name="Sample Sales",
            description="Synthetic sales data with missing values and outliers.",
            source_type=SourceType.csv,
            file_path=str(dest),
            status=DatasetStatus.ready,
            row_count=int(len(cleaned)),
            column_count=int(cleaned.shape[1]),
            schema_json=profiling_service.build_schema(cleaned),
            owner_id=user.id,
        )
        db.add(dataset)
        db.commit()
        logger.info("Seeded sample dataset with %d rows." % len(cleaned))
    finally:
        db.close()


if __name__ == "__main__":
    seed()
