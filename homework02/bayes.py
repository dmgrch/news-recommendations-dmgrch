from math import log
from collections import defaultdict, Counter


class NaiveBayesClassifier:
    """Class implements a naive Bayesian classifier"""

    def __init__(self, alpha=0.05):
        self.alpha = alpha
        self._classes = None
        self._class_probs = None
        self._word_probs = None
        self._vocab = None

    def fit(self, X, y):
        """Fit Naive Bayes classifier according to X, y."""
        self._classes = list(set(y))
        class_counts = Counter(y)
        total = sum(class_counts.values())
        self._class_probs = {cls: class_counts[cls] / total for cls in self._classes}

        word_counts_per_class = {cls: defaultdict(int) for cls in self._classes}
        self._vocab = set()
        total_words_per_class = {cls: 0 for cls in self._classes}

        for label, text in zip(y, X):
            for word in text.split():
                self._vocab.add(word)
                word_counts_per_class[label][word] += 1
                total_words_per_class[label] += 1

        self._word_probs = {cls: {} for cls in self._classes}
        d = len(self._vocab)

        for cls in self._classes:
            n_c = total_words_per_class[cls]
            for word in self._vocab:
                n_i_c = word_counts_per_class[cls].get(word, 0)
                self._word_probs[cls][word] = (n_i_c + self.alpha) / (n_c + self.alpha * d)

    def predict(self, X):
        """Perform classification on an array of test vectors X."""
        preds = []
        d = len(self._vocab)

        for text in X:
            scores = {}
            for cls in self._classes:
                scores[cls] = log(self._class_probs[cls])

                for word in text.split():
                    if word in self._vocab:
                        prob = self._word_probs[cls].get(word)
                        if prob:
                            scores[cls] += log(prob)
                        else:
                            n_c = sum(self._word_probs[cls].values())
                            scores[cls] += log(self.alpha / (n_c + self.alpha * d))

            preds.append(max(scores, key=scores.get))
        return preds

    def score(self, X_test, y_test):
        """Returns the mean accuracy on the given test data and labels."""
        preds = self.predict(X_test)
        results = [1 if label == preds[i] else 0 for i, label in enumerate(y_test)]
        accuracy = results.count(1) / len(results)
        return accuracy
