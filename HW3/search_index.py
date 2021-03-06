from collections import Counter
from nltk.stem.porter import PorterStemmer
from nltk import word_tokenize
from math import log10, sqrt
from pprint import pprint
import cPickle as pickle
import heapq


class SearchIndex:
    def __init__(self, dictionary_file, postings_file):
        with open(dictionary_file, 'rb') as dfile:
            self.dictionary = pickle.load(dfile)
        self.postings = open(postings_file, 'rb')
        self.stemmer = PorterStemmer()
        with open('FILE_COUNT', 'rb') as fcount:
            self.N = int(fcount.read())

    def get_postings(self, term):
        """ Get postings list for a given term """
        if term in self.dictionary:
            self.postings.seek(self.dictionary[term][1])
            results = pickle.load(self.postings)
            return results
        return []

    @classmethod
    def cal_log_tfs(self, freq):
        return 1 + log10(freq) if freq else 0

    def cal_idf(self, term):
        return log10(self.N/self.dictionary[term][2]) \
            if term in self.dictionary else 0

    def tfs_idf(self, term, freq):
        return self.cal_log_tfs(freq) * self.cal_idf(term)

    def normalize_vector(self, terms, weight_function):
        """ Normalize vector, using a given weight_function."""
        factor = 0
        for key, value in terms.iteritems():
            weight = weight_function(key, value)
            terms[key] = weight
            factor += weight ** 2
        return {key: (value/factor)
                for key, value in terms.iteritems()} if factor else {}

    @staticmethod
    def to_result_string(heap):
        return " ".join(str(x[1]) for x in heap) if heap else ""

    def search(self, query):
        """ Entry point of search
        - case-folding and stemming
        - calculate weights for each query term (tf * idf)
        - normalize query vector
        - normalize doc vector and compute cosine score
        - put scores in a heap and get the top ten scores
        """
        terms = map(lambda x: self.stemmer.stem(x.lower()), word_tokenize(query))
        terms = dict(Counter(terms))
        query_vector = self.normalize_vector(terms, self.tfs_idf)
        if not any(query_vector):
            return ""

        scores = {}
        denom = {}
        for term, value in query_vector.iteritems():
            postings = self.get_postings(term)
            for p in postings:
                doc, tf, weight_td = p[0], p[1], p[2]
                if doc in scores:
                    scores[doc] += weight_td * value
                    denom[doc] += weight_td ** 2
                else:
                    scores[doc] = weight_td * value
                    denom[doc] = weight_td**2


        search_results = []
        for doc, value in scores.iteritems():
            scores[doc] = value/sqrt(denom[doc])
            heapq.heappush(search_results, (-scores[doc], int(doc))) # heapq is a min-heap
        top_ten = heapq.nsmallest(10, search_results)
        return SearchIndex.to_result_string(top_ten)
