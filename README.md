# Purpose
 * Analyze iBatis/myBatis xml
 * Extract SQLs
 * Find SQLs that contains some field and columns
 * Find SQLs that contains LIKE comparison
 
# How to use this
## Prerequisites
 * python3
 * git
```bash
[ec2-user@192.168.0.1 /home/ec2-user]$ sudo yum install -y python36
[ec2-user@192.168.0.1 /home/ec2-user]$ sudo yum install -y git 
```

## Run script
```bash
[ec2-user@192.168.0.1 /home/ec2-user]$ git clone https://github.com/yikster/parse-ibatis
[ec2-user@192.168.0.1 /home/ec2-user]$ cd parse-ibatis
[ec2-user@192.168.0.1 /home/ec2-user/parse-ibatis]$ python3 parse-ibatis.py -p /home/ec2-user/data 
```
### result
```bash
Summary
345 files are tested in /home/ec2-user/data
1678 XML files are tested
4000 SQL files are tested
5678 queries are tested.
100 queries has LIKE.
10  unique table.columns are found.
5 unique tabls are found.

Unique Table Column List...
	 0 TABLE_A.column_1
	 1 TABLE_B.column_2
	 2 TABLE_B.column_3
	 3 TABLE_C.column_4
	 4 TABLE_D.column_5
	 5 TABLE_E.column_6
	 6 TABLE_F.column_7
	 7 TABLE_G.column_8
	 8 TABLE_H.column_9
	 9 TABLE_I.column_10
	 
	 
All Query List using LIKE...
     1. TABLE_A.column_1
        1-01. file_sql_id SELECT /* xmlfile.queryid */ field1, field2 FROM ...
        1-02. file_sql_id SELECT /* xmlfile.queryid */ field1, field2 FROM ...
        1-03. file_sql_id SELECT /* xmlfile.queryid */ field1, field2 FROM ...
	 
```

## Versioning
0.1 Find queries using LIKE in directory

## Authors
Kyoungsu Lee