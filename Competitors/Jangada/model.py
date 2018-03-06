from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import LabelEncoder, StandardScaler
from scripts.utils import AnnotatedEmails, AnnotatedEmail
from scripts.utils import denotation_types
from scripts.Jangada.features import mail2features
from scripts.Jangada.cperceptron import CollinsPerceptron
import pandas as pd
import numpy as np
from pprint import pprint
from collections import Counter
from sklearn.utils import compute_class_weight


def flatten(lst):
    return [l for sub in lst for l in sub]


if __name__ == '__main__':
    # folder = "../../data/enron/annotated/"
    folder = "../../data/asf/annotated/"
    for perturb in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
        print('=============================================================')
        print('PERTURBATION:', perturb)
        emails = AnnotatedEmails(folder, mail2features, perturbation=perturb)
        print('loaded mails')
        zones = 2

        X_train, X_test, X_eval = emails.features
        print('loaded features')
        le = LabelEncoder()
        le.fit(AnnotatedEmail.zone_labels(zones))
        print(le.classes_)
        if zones == 5:
            y_train, y_test, y_eval = emails.five_zones_labels
        else:
            y_train, y_test, y_eval = emails.two_zones_labels
        class_weights = compute_class_weight('balanced', le.classes_, flatten(y_train))
        print('loaded labels')

        cp = CollinsPerceptron(5, 'model')

        if perturb == 0.0 and True:
            cp.fit(X_train, y_train, 40)

        print('fitted')
        y_pred = cp.predict(X_test, y_test)
        print('predicted')

        # pprint(list(zip(flatten(y_pred), flatten(y_test))))
        a = le.transform(flatten(y_pred))
        b = le.transform(flatten(y_test))
        print(Counter(flatten(y_pred)))
        print(Counter(flatten(y_test)))
        print('Accuracy: ', accuracy_score(b, a))
        print(classification_report(b, a, target_names=le.classes_))
        print('Accuracy (weighted): ', accuracy_score(b, a, sample_weight=[class_weights[s] for s in b]))
        print(classification_report(b, a, target_names=le.classes_, sample_weight=[class_weights[s] for s in b]))
        # pprint(precision_recall_fscore_support(b, a))
        print(confusion_matrix(b, a))
