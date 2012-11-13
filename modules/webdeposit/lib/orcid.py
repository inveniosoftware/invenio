import subprocess
import json

class OrcidSearch:

    def search_authors(self, query):
        query = query.replace(" ", "+")
        p = subprocess.Popen("curl -H 'Accept: application/orcid+json' \
                             'http://devsandbox.orcid.org/search/orcid-bio?q=" + \
                             query + "&start=0&rows=10'", \
                             shell=True, \
                             stdout=subprocess.PIPE, \
                             stderr=subprocess.STDOUT)
        jsonResults = ""
        for line in p.stdout.readlines():
            jsonResults = line

        self.authorsDict = json.loads(jsonResults)

    def get_authors_names(self):
        author_names = []
        try:
            for author in self.authorsDict['orcid-search-results']['orcid-search-result']:
                given_name = author['orcid-profile']['orcid-bio']['personal-details']['given-names']['value']
                family_name = author['orcid-profile']['orcid-bio']['personal-details']['family-name']['value']
                name = family_name + " " + given_name
                author_names.append(name)
            return author_names
        except KeyError:
            return []
