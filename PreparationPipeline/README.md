## Pipeline
The pipeline uses [JUST](https://github.com/isi-nlp/JUST) to wrap the different scripts.

Execute the pipeline like so:
```bash
python3 just/just.py pipeline.just
```

## GraphML Skript
Assuming default options: 
```
python scripts/build_graphml.py --people data/people.txt --quagga-parsed data/parsed_enron.json --graph data/enron.graphml --include-text
```

## TinkerPop Gremlin tips
```
graph = TinkerGraph.open()
graph.io(IoCore.graphml()).readGraph("/path/to/graph.graphml")
g = graph.traversal()

# who has the most aliases
g.V().hasLabel('alias').groupCount().by('pID').unfold().order().by(values,decr).limit(10)

# see the actual list of aliases for some people
g.V().hasLabel('person').order().by(outE().hasLabel('alias').count(), decr).limit(5).out('alias').group().by('pID').by('name').unfold().skip(3)
g.V().hasLabel('person').order().by(outE().hasLabel('alias').count(), decr).out('alias').group().by('pID').by('name').unfold().skip(10).limit(5)
```

## GraphML structure 

```mermaid
graph TD
P1(PERSON == type:person, labelV:person, pID)
P1-->|labelE:alias| A11[ALIAS == type:alias,labelV:alias,pID, name]

P2(PERSON)
P2-->|alias|A21[ALIAS]
P2-->|alias|A22[ALIAS]
P2-->|alias|A23[ALIAS]

P3[PERSON]
P4[PERSON]
P5[PERSON]

M1(EMAIL == type:email, subject, sent, block_type, text, labelV:email, original:an id)
M11(EMAIL duplicate == type:email, subject, sent, block_type, text, labelV:duplicate, original:an id)
M2(EMAIL == type:email, subject, sent, block_type, text, labelV:email, original:an id)
M3(EMAIL == type:email, subject, sent, block_type, text, labelV:email, original:an id)
M31(EMAIL dupliate)
M32(EMAIL dupliate)
M33(EMAIL dupliate)

P1-->|sender| M1
M1-->|recipient, rec_type:to|P2
P2-->|sender|M2
M2-->|recipient,rec_type:to|P1
M2-->|recipient,rec_type:cc|P3
P3-->|sender|M3
M3-->|recipient|P1
M3-->|recipient|P4
M3-->|recipient|P5

M1-->M11
M3-->M31
M3-->M32
M3-->M33

M1-->|conversation|M2
M2-->|conversation| M3
```