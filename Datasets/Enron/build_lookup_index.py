from datetime import datetime, timezone
from .utils import Emails
import re

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class EnronMail(Base):
    __tablename__ = 'enron_mail'
    id = Column(Integer, primary_key=True)
    mid = Column(String)
    mailbox = Column(String)
    folder = Column(String)
    path = Column(String)
    sender = Column(String)
    xsender = Column(String)
    to = Column(String)
    xto = Column(String)
    cc = Column(String)
    xcc = Column(String)
    bcc = Column(String)
    xbcc = Column(String)
    subject = Column(String)
    date = Column(DateTime)

    def __repr__(self):
        return "<User(id=%s, from='%s[%s]', date='%s', path='%s')>" % (
            self.id, self.sender, self.xsender, self.date, self.path)


if __name__ == "__main__":
    # takes about 30min
    # > tree -d enron/data/original | wc -l
    # > 520903
    engine = create_engine('sqlite:///mails.db', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for i, mail in enumerate(Emails('../../enron/data/original/')):
        session.add(EnronMail(mid=mail.id, mailbox=mail.mailbox, folder=mail.folder,
                              path=mail.file,
                              sender=mail.sender, xsender=mail.xsender,
                              to=mail.to, xto=mail.xto,
                              bcc=mail.bcc, xcc=mail.xcc,
                              cc=mail.cc, xbcc=mail.xbcc,
                              subject=mail.subject,
                              date=mail.sent))
        if i % 1000 == 0:
            print('commit', i)
            session.commit()
