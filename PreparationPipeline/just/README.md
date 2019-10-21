"just" facilitates the construction and management of bash based pipelines on a cluster by 
* Grouping commands under a task name/id
* Sharing global variables among tasks (for example paths to common programs)
* Easily scheduling tasks as jobs on a cluster (supports job dependency for tasks with consecutive ids)

<b>Reasons to use "just"</b>:
* Modularity and reusable code: shorter debug cycles
* Reproducibility: don't struggle with your own scripts 3 months from now.
* qsub logging
  * STDOUT/STDERR are logged into files with meaningful names, indicating the task they belong to.
  * qsub logs are synced to the master node
 


<b>Usage</b>:
* Define a sequence of indexed tasks in a file (here named 'tasks.just'):

<pre>
0:shared_commands:{{
  # anything written here is shared by all tasks at execution time.
  A=1
}}

1:write:{{
  echo $A >> $workdir/1.txt 
  # the variable $A is known here since it is defined in task 0
  # $workdir should be defined by the user at the command line
}}

2:read:{{
  cat $workdir/1.txt
}}
</pre>

* <b>Execute on current machine</b>: just.py tasks.just -s 1-2 --workdir test_just
* <b>Schedule on a cluster</b>: just.py tasks.just -s 1-2 --workdir test_just --q $QUEUE_NAME (e.g. -q '*@@nlp' on ND's CRC)