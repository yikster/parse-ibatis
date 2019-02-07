import argparse
import xml.etree.ElementTree as xml
import logging, sys
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logging.debug('Debugging is started!')

#logging.info('We processed %d records', len(processed_records))

def readfiles(file_path, pattern):
    import glob

    return glob.glob(file_path + "/**/" + pattern, recursive=True)

def find_where_and_from(column, lines, index):
    i = index
    find_where = -1
    find_from = -1

    while i > 0:
        if find_where == -1 and "WHERE" in lines[i]:
            find_where = i
        if find_where != -1 and "FROM" in lines [i]:
            find_from = i
            break
        i = i - 1

    from_where = []

    logging.debug("find_where={}, find_from={}".format(find_where, find_from))
    if find_where == find_from and find_where != -1:
        logging.debug("Line:" + lines[find_where])
        end = lines[find_where].rfind("WHERE")
        start = lines[find_where][:end].rfind("FROM")
        logging.debug("start={}, end={}".format(start, end))
        from_where = lines[find_where][start:end].split()
    elif find_where > -1 and find_from > -1:
        from_where = lines[find_from:find_where]

    logging.debug("FROM_WHERE=" + str(from_where))
    table_name = ""
    if 0 < len(from_where):
        froms = " ".join(from_where).split()
        logging.debug("Froms:" + str(froms))


        if "." in column:
            table_alias = column.split(".")[0]

            for idx, alias in enumerate(froms):
                if table_alias == alias:
                    table_name = froms[idx - 1]

        else:
            table_name = froms[1]


        logging.debug("TableName: " + table_name)
    else:
        sys.exit()

    sql = ""
    if len(table_name) == 0:
        sql = " ".join(lines)

    return table_name, sql



def extract_alias(column):
    if "." in column:
        return column.split(".")[1]
    else:
        return column

def parseXML(file):
    doc = None
    try:
        doc = xml.parse(file)
    except Exception as ex:
        print("Errors in parsing [{}]".format(file))
        print(ex)
        sys.exit()

    root = doc.getroot()

    result = []

    select = root.findall(".//select")
    sql = root.findall("..sql")
    update = root.findall(".//update")
    delete = root.findall(".//delete")
    insert = root.findall(".//insert")

    elements = []
    elements.extend(select)
    elements.extend(sql)
    elements.extend(update)
    elements.extend(delete)
    elements.extend(insert)

    total_elements = len(elements)
    for e in elements: #root.findall(".//select"):
        upper = e.text.upper()
        if "LIKE" in upper and '%' in upper:
            logging.debug(file)
            logging.debug(e.attrib['id'])
            logging.debug(e.text)
            ## Like가 포함된 line ckwrl

            lines = e.text.split("\n")
            for i, line in enumerate(lines):
                if "LIKE" in line.upper():
                    #print(i, line)
                    words = line.upper().split("LIKE")
                    column = words[0].split()[-1]
                    logging.debug("Column:" +column)
                    table, sql = find_where_and_from(column, lines, i)

                    row = {"filename": file,
                           "queryid": e.attrib['id'],
                           "table": table,
                           "column": extract_alias(column),
                           "like_pharase": line,
                           "sql": sql
                    }
                    result.append(row)

    return total_elements, len(result), result

'''
    for e in root.findall(".//sql"):
        upper = e.text.upper()
        if "LIKE" in upper and '%' in upper:
            print(file)
            print(e.attrib['id'])
            print(e.text)


'''

def main():
    parser = argparse.ArgumentParser(description='Parse iBatis xml files in path.')
    parser.add_argument('--path', "-p")

    args = parser.parse_args()

    files = readfiles(args.path, "*.xml")

    all = []
    total_query_count = 0
    total_like_query_count = 0
    for file in files:
    #print(file)
        query_count, like_query_count, result = parseXML(file)
        total_query_count += query_count
        total_like_query_count += like_query_count

        all.extend(result)

#print(all)

    table_column = []
    table_sqls = {}
    for e in all:
        key = e["table"].upper() + "." + e["column"].lower()
        table_column.append(key)
        table_sqls[key] = e["sql"]

    uniquelist = set(table_column)
    unique_table_columns = len(uniquelist)


    print("Summary")
    print(len(files), "files are tested in", args.path)
    print(total_query_count, "queries are tested.")
    print(total_like_query_count, "queries has LIKE.")
    print("But, unique_table_columns is", unique_table_columns)
    print("Unique Table Column List...")
    for i, item in enumerate(sorted(uniquelist)):
        print("\t",i, item, "!!! Check SQL!!! \n" + table_sqls[item] + "\n" if item.startswith(".") else " ")



main()