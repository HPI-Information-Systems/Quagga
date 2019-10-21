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