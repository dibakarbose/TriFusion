#!/usr/bin/python2

import sqlite3 as lite
import os


def printInparalogsFile (cur, filename):

    cur.execute("select taxon_id, sequence_id_a, sequence_id_b, normalized_score\
        from InParalog\
        order by taxon_id, sequence_id_a, sequence_id_b asc")

    file_fh = open(filename, "w")

    with file_fh:
        while True:

            row = cur.fetchone()
            if row is None:
                break

            file_fh.write("{}\t{}\t{}\n".format(row[1],
                                                row[2],
                                                str((float(row[3]) * 1000 + .5) / 1000)))


################################################################


def printOrthologsFile (cur, filename):

    cur.execute("select taxon_id_a, taxon_id_b, sequence_id_a, sequence_id_b, normalized_score\
        from Ortholog\
        order by taxon_id_a, taxon_id_b, sequence_id_a, sequence_id_b asc")

    file_fh = open(filename, "w")

    with file_fh:
        while True:

            row = cur.fetchone()
            if row is None:
                break

            file_fh.write("{}\t{}\t{}\n".format(row[2],
                                                row[3],
                                                str((float(row[4]) * 1000 + .5) / 1000)))

################################################################


def printCoOrthologsFile (cur, filename):

    cur.execute("select taxon_id_a, taxon_id_b, sequence_id_a, sequence_id_b, normalized_score\
        from CoOrtholog\
        order by taxon_id_a, taxon_id_b, sequence_id_a, sequence_id_b asc")

    file_fh = open(filename, "w")

    with file_fh:
        while True:

            row = cur.fetchone()
            if row is None:
                break

            file_fh.write("{}\t{}\t{}\n".format(row[2],
                                                row[3],
                                                str((float(row[4]) * 1000 + .5) / 1000)))

################################################################


def printMclAbcFile (cur, filename):

    cur.execute("select sequence_id_a, sequence_id_b, normalized_score\
        from InParalog\
        union\
        select sequence_id_a, sequence_id_b, normalized_score\
        from Ortholog\
        union\
        select sequence_id_a, sequence_id_b, normalized_score\
        from CoOrtholog")

    file_fh = open(filename, "w")

    with file_fh:
        while True:

            row = cur.fetchone()
            if row is None:
                break

            file_fh.write("{}\t{}\t{}\n".format(row[0],
                                                row[1],
                                                str((float(row[2]) * 1000 + .5) / 1000)))


def execute(db_dir, dest):
    con = lite.connect(os.path.join(db_dir, "orthoDB.db"))

    with con:

        cur = con.cursor()

        printOrthologsFile(cur, os.path.join(dest, "backstage_files",
                                             "orthologs.txt"))

        printInparalogsFile(cur, os.path.join(dest, "backstage_files",
                                              "inparalogs.txt"))

        printCoOrthologsFile(cur, os.path.join(dest, "backstage_files",
                                               "coorthologs.txt"))

        printMclAbcFile(cur, os.path.join(dest, "backstage_files",
                                          "mclInput"))

if __name__ == "__main__":
    execute(".", ".")

__author__ = "Fernando Alves and Diogo N. Silva"