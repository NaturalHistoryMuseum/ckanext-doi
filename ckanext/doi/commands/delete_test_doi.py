
import logging

from ckan.lib.cli import CkanCommand
from ckanext.doi.model import DOI
from ckanext.doi.config import TEST_PREFIX
from ckan.model import Session


log = logging.getLogger(__name__)

class DeleteTestDOICommand(CkanCommand):
    """

    Delete all test DOIs

    paster delete-test-doi -c /etc/ckan/default/development.ini

    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def command(self):

        print 'Deleting all test DOIs'

        self._load_config()
        Session.query(DOI).filter(DOI.identifier.like('%' + TEST_PREFIX + '%')).delete(synchronize_session=False)
        Session.commit()

