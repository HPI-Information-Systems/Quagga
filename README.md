# Quagga
An email segmentation system:
- reference implementation of ECIR 2018 paper
- annotated datasets
  - newly collected ASF email corpus, annotated by email zones only
  - selection of Enron corpus, annotated by email zones only
  - selection of Enron corpus, detailled annotation (including names, aliases, metadata)
  - annotated using [Enno](https://github.com/TimRepke/enno), util classes to read format included here

# Reference

> Repke, Tim and Krestel R. *Bringing Back Structure to Free Text Email Conversations with Recurrent Neural Networks.* ECIR 2018

### Abstract
Email communication plays an integral part of everybody’s
life nowadays. Especially for business emails, extracting and analysing
these communication networks can reveal interesting patterns of processes
and decision making within a company. Fraud detection is another
application area where precise detection of communication networks is
essential. In this paper we present an approach based on recurrent neural
networks to untangle email threads originating from forward and reply
behaviour. We further classify parts of emails into 2 or 5 zones to capture
not only header and body information but also greetings and signatures.
We show that our deep learning approach outperforms state-of-the-art
systems based on traditional machine learning and hand-crafted rules.
Besides using the well-known Enron email corpus for our experiments,
we additionally created a new annotated email benchmark corpus from
Apache mailing lists.

# Setup
### Installation
Install the dependencies from requirements.txt into your virtualenv. Tested on Python 3.6.5.
- todo, this section is gonna change once on we're on pypi.

### Running
Make sure to call using  ```python -m Quagga.[file to execute]``` from top-level directory, otherwise the imports won't work.


# Related Work Sources
- Original Code for [Jangada](http://www.cs.cmu.edu/~vitor/software/jangada/), Carvalho, 2004
- More infos and data for [Jangada](http://www.cs.cmu.edu/~vitor/codeAndData.html) (600+ annotated mails in 20 newsgroup dataset)
- [MinorThird](http://minorthird.sourceforge.net/) Library used by Jangada
- 400 [annotated emails](http://zebra.thoughtlets.org/data.php) by Lampert et. al (Enron data)
- [Zebra](http://zebra.thoughtlets.org/zoning.php) System for email zoning
- Another implementation of [Zebra](https://github.com/gerhardgossen/soZebra)
- [Talon](https://github.com/mailgun/talon) is an awesome universal tool for everything that has to do with email structure


