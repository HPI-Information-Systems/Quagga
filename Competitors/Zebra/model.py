from sklearn.svm import LinearSVC, SVC
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import LabelEncoder, StandardScaler
from scripts.utils import AnnotatedEmails, AnnotatedEmail
from scripts.utils import denotation_types
from scripts.Zebra.features import mail2features
import pandas as pd
import numpy as np
from sklearn.utils import compute_class_weight


def flatten(lst):
    return [l for sub in lst for l in sub]


def to_array(lst, cols=None):
    df = pd.DataFrame(lst, columns=cols)
    df.fillna(0, inplace=True)
    if cols is not None:
        return np.nan_to_num(df.as_matrix(cols))
    return df.columns, df.as_matrix()


if __name__ == '__main__':
    folder = "../../data/enron/annotated/"
    # folder = "../../data/asf/annotated/"

    zones = 5
    svc = SVC(max_iter=200, random_state=42, verbose=1)  # , class_weight='balanced')  # , class_weight={0: 1.0, 1: 0.5}

    for perturb in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
        print('=============================================================')
        print('PERTURBATION:', perturb)
        emails = AnnotatedEmails(folder, mail2features, perturbation=perturb)
        print('loaded mails')

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
        # y_train, y_test, y_eval = emails.two_zones_labels
        print('loaded labels')

        if perturb == 0.0 and True:
            ss = StandardScaler()
            cols, X_train = to_array(flatten(X_train))
            X_train = ss.fit_transform(X_train)
        else:
            X_train = ss.transform(to_array(flatten(X_train), cols))
        X_test = ss.transform(to_array(flatten(X_test), cols))
        X_eval = ss.transform(to_array(flatten(X_eval), cols))

        y_train = le.transform(flatten(y_train))
        y_test = le.transform(flatten(y_test))
        y_eval = le.transform(flatten(y_eval))

        print('train', X_train.shape)
        print('test', X_test.shape)
        print('eval', X_eval.shape)

        xt = X_test
        yt = y_test

        if perturb == 0.0 and True:
            svc.fit(X_train, y_train)
            print('fitted')

        y_pred = svc.predict(xt)
        print('predicted')

        print(le.classes_)

        print('Accuracy: ', accuracy_score(yt, y_pred))
        print(classification_report(yt, y_pred, target_names=le.classes_))
        print('Accuracy (weighted): ', accuracy_score(yt, y_pred, sample_weight=[class_weights[s] for s in yt]))
        print(classification_report(yt, y_pred, target_names=le.classes_, sample_weight=[class_weights[s] for s in yt]))
        print(confusion_matrix(yt, y_pred))
