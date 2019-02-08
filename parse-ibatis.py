import argparse
import xml.etree.ElementTree as ElementTree
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logging.debug('Debugging is started!')


def get_files(file_path, pattern):
    import glob

    return glob.glob(file_path + "/**/" + pattern, recursive=True)


def find_where_and_from(column, lines, index):
    i = index
    find_where = -1
    find_from = -1

    while i > 0:
        if find_where == -1 and "WHERE" in lines[i]:
            find_where = i
        if find_where != -1 and "FROM" in lines[i]:
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

    sql = " ".join(lines).replace("  ", "").strip()

    return table_name, sql


def extract_alias(column):
    if "." in column:
        return column.split(".")[1]
    else:
        return column


def parse(file):
    if file.upper().endswith(".XML"):
        return parse_xml(file)
    elif file.upper().endswith(".SQL"):
        return parse_sql(file)


def parse_sql(file):
    f = open(file)
    lines = [line.rstrip('\n') for line in f]

    result = parse_one_sql(lines, file, file, " ".join(lines).rstrip())
    total_elements = 1  # sql file has only one sql
    total_like_queries = len(result)
    return total_elements, total_like_queries, result


def parse_xml(file):

    try:
        doc = ElementTree.parse(file)
    except Exception as ex:
        print("Errors in parsing [{}]".format(file))
        print(ex)
        sys.exit()

    root = doc.getroot()

    result = []

    select = root.findall(".//select")
    sql = root.findall("..//sql")
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
    for e in elements:
        upper = e.text.upper()
        if "LIKE" in upper and '%' in upper:
            logging.debug(file)
            logging.debug(e.attrib['id'])
            logging.debug(e.text)
            sql_lines = upper.split("\n")
            sql_id = e.attrib['id']

            result.extend(parse_one_sql(sql_lines, sql_id, file, " ".join(e.text.split("\n")).replace("  ", "").rstrip()))

    return total_elements, len(result), result


def parse_one_sql(sql_lines, sql_id, file, raw_sql):
    result = []
    for i, line in enumerate(sql_lines):
        if "LIKE" in line.upper():

            words = line.upper().split("LIKE")
            column = words[0].split()[-1]
            logging.debug("Column:" + column)
            table, sql = find_where_and_from(column, sql_lines, i)

            row = {"filename": file,
                   "query_id": sql_id,
                   "table": table,
                   "column": extract_alias(column),
                   "likes": line,
                   "sql": raw_sql.encode("utf-8")
                   }
            result.append(row)
    return result


def main():
    parser = argparse.ArgumentParser(description='Parse iBatis xml files in path.')
    parser.add_argument('--path', "-p")

    args = parser.parse_args()

    files = get_files(args.path, "*.xml")
    files.extend(get_files(args.path, "*.sql"))

    total_query_count = 0
    total_like_query_count = 0

    xml_file_count = 0
    sql_file_count = 0

    all_data = []

    for file in files:
        query_count, like_query_count, result = parse(file)
        total_query_count += query_count
        total_like_query_count += like_query_count
        if file.upper().endswith(".XML"):
            xml_file_count += 1
        elif file.upper().endswith(".SQL"):
            sql_file_count += 1

        all_data.extend(result)

    table_column = []
    sql_list = {}

    unique_tables = {}
    for e in all_data:
        key = e["table"].upper() + "." + e["column"].lower()
        unique_tables[e["table"]] = e["table"]
        table_column.append(key)
        if key not in sql_list.keys():
            sql_list[key] = []

        sql_file_id = e['filename'] + "..." + e['query_id']
        sql_list[key].append({"key": key, "sql_file_id": sql_file_id, "sql": e["sql"]})

    unique_table_column = set(table_column)

    print("Summary")
    print("--------------------------------------------")
    print(len(files), "files are tested in", args.path)
    print(xml_file_count, "XML files are tested.")
    print(sql_file_count, "SQL files are tested.")
    print(total_query_count, "queries are tested.")
    print(total_like_query_count, "queries has LIKE.")
    print(len(unique_table_column), " unique table.columns are found.")
    print(len(unique_tables), " unique tables are found.", )

    print("\n\n\nUnique Table Column List...")
    print("--------------------------------------------")
    print("\tNo\tTABLE.column\tsql_counts\tfile_sql_id(first)\tsql(first)")
    for i, key in enumerate(sorted(unique_table_column)):
        print("\t%2d. %s\t%2d\t%s\t%s%s" %
              (i + 1,
               key,
               len(sql_list[key]),
               sql_list[key][0]["sql_file_id"],
               "/* !!! Check SQL!!! */ " if key.startswith(".") else "",
               sql_list[key][0]["sql"][:80 if len(sql_list[key][0]["sql"]) > 80 else -1]))

    print("\n\n\nAll Query Lists using LIKE")
    print("--------------------------------------------")
    for i, key in enumerate(sorted(unique_table_column)):
        print("%2d.\t%s" % (i + 1, key))
        for j, data in enumerate(sql_list[key]):
            print("\t%2d-%02d.\t%s\t%s" %
                  (i + 1,
                   j + 1,
                   data["sql_file_id"],
                   data["sql"]))


main()

