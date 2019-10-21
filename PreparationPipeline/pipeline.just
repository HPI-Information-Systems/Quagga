0:shared_commands:{{
  ORIGINAL_ENRON_DIRECTORY=enron
  QUAGGA_RESULT=parsed_enron
  CONCAT_QUAGGA=parsed_enron.json
  RAW_ALIASES=raw_aliases.json
  MATCHED_ALIASES=people.txt
  GRAPHML=enron.graphml

  source venv/bin/activate
}}

1:write:{{
  #echo $A >> $workdir/1.txt
  # the variable $A is known here since it is defined in task 0
  # $workdir should be defined by the user at the command line
}}

2:read:{{
  #cat $workdir/1.txt
}}

3:quagga:{{
  python3 scripts/enron_quagga.py --input_dir $workdir/$ORIGINAL_ENRON_DIRECTORY --output_dir $workdir/$QUAGGA_RESULT
}}

4:concat_quagga_results:{{
  for i in $(ls $workdir/$QUAGGA_RESULT); do (cat $workdir/$QUAGGA_RESULT/$i; echo) >> $workdir/$CONCAT_QUAGGA; done
}}

5:person_deduplication:{{
    cd scripts/personDeduplication
    sbt assembly
    cd ../..
    echo "You need to manually ship the jar to the server (sopedu), put $CONCAT_QUAGGA on hdfs"
    spark-submit --class "org.benhurdelhey.PersonDeduplicator" --conf spark.driver.cores=4 --conf spark.executor.memory=2g --conf spark.logConf=true --master yarn\
     scripts/personDeduplication/target/scala-2.10/PersonDeduplicator-assembly-1.0.jar $workdir/$CONCAT_QUAGGA $workdir/mincutcheckpoint $workdir/$MATCHED_ALIASES/ $workdir/split
}}

6:build_graphml:{{
  python scripts/build_graphml.py --people $workdir/$MATCHED_ALIASES \
                                  --quagga-parsed $workdir/CONCAT_QUAGGA \
                                  --graph $workdir/$GRAPHML
}}

7:list_results:{{
  ls -lisah $workdir
}}
