# Enron
## build index
see script in scripts folder

 takes about 30min
```bash
$ tree -d enron/data/original | wc -l
52903
```
the index may contain duplicates. to remove them, run
```bash
$ sqlite3 mails.db 'SELECT a.id, b.id, a.sender, b.sender, (julianday(a.date)-julianday(b.date))*24 as diff, a.`to`, b.`to` FROM enron_mail a, enron_mail b WHERE a.id<b.id and a.split is not null and b.split is not null and abs(diff)<0.007' > results.txt
$ cat results.txt | cut -d '|' -f2 | grep "^[0-9]\+$" | sort -n | uniq -u | awk '{ print "UPDATE enron_mail SET exclude=1 WHERE id="$1";" }' > updates.sql
$ sqlite3 mails.db updates.sql
```

## Train/Test/Eval
Set for training, development testing and final evaluation are first split by mailbox as follows:

- **TRAIN:** ("pimenov-v","scholtes-d","arora-h","mims-p","mckay-b","mccarty-d","ring-a","wolfe-j","geaccone-t","parks-j","whalley-l","williams-w3","buy-r","dean-c","hernandez-j","giron-d","sager-e","haedicke-m","kitchen-l","lokay-m","rogers-b","scott-s","nemec-g","symes-k","beck-s","shackleton-s","jones-t","dasovich-j") 
- **TEST:** ("rapp-b","gang-l","staab-t","townsend-j","may-l","lewis-a","horton-s","skilling-j","sanders-r","germany-c","mann-k","kaminski-v")
- **EVAL:**("gilbertsmith-d","weldon-v","semperger-c","pereira-s","forney-j","heard-m","presto-k","grigsby-m","davis-d","mcconnell-m","bass-e","farmer-d","taylor-m","kean-s")

This selection is done by hand and more or less random. Each set contains mailboxes of varying size across the full range from small to large.

```sql
select exclude as ex, split as sp, count(1) as cnt from enron_mail group by sp, ex order by sp, ex
```

| Split     | Count  | Count (uniq) |
|-----------|--------|--------------|
| 2 - EVAL  | 76295  | 59396        |
| 1 - TEST  | 83946  | 64509        |
| 0 - TRAIN | 165312 | 116226       |
| IGNORE    | 191448 | -            |

## Annotation
Random sampling from above split by:
```sql
UPDATE enron_mail
SET to_annotate=1
WHERE id IN (SELECT id FROM enron_mail WHERE split=2 and enron_mail.exclude ISNULL ORDER BY RANDOM() LIMIT 100)
```
- Sample sizes for split 0: 500, 1: 200, 2: 100; Total: 800
- Selected mails for annotation in `data/enron/annotation_index.csv`

Copy them to brat data directory:
```bash
cat email-splitting/data/enron/annotation_index.csv | grep  "^2" | cut -d, -f5 | while read line; do cp enron/data/original/$line email-splitting/tools/brat/data/enron/eval/$(echo $line| tr / _)txt ; done
```


# Apache Dataset
http://mail-archives.apache.org/mod_mbox/

EVAL: 50 mails from flink-user
TEST: 100 mails from groovy-users
TRAIN: 250 mails form hadoop-user

Randomly select last mail of a thread within 2017.

# Other Datasets
https://news.ycombinator.com/item?id=2165497
