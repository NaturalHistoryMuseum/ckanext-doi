FROM naturalhistorymuseum/ckantest:0.1

# ckan is installed in /base/src/ckan in the ckan-dev image we're basing this image on
WORKDIR /base/src/ckanext-doi

# copy over the ckanext-doi source
COPY . .

# install the dependencies
RUN python setup.py develop && \
    pip install -r requirements.txt && \
    pip install -r dev_requirements.txt

# this entrypoint ensures our service dependencies (postgresql, solr and redis) are running before
# running the cmd
ENTRYPOINT ["/bin/bash", "/opt/waits/basic.sh"]

# run the tests with coverage output
CMD ["pytest", "--cov=ckanext.doi", "--ckan-ini=test.ini", "tests"]
