import pytest

from ckanext.doi.model.doi import doi_table

try:
    # 2.11 compatibility
    from ckan.model import ensure_engine
except ImportError:

    def ensure_engine():
        return None


@pytest.fixture
def with_doi_table(reset_db):
    """
    Simple fixture which resets the database and creates the doi table.
    """
    reset_db()
    engine = ensure_engine()
    doi_table.create(engine, checkfirst=True)
