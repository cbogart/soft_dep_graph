import csv
import pickle
import numpy
import math
import time
from collections import defaultdict
from sklearn.metrics.cluster import normalized_mutual_info_score
from scipy.stats import pearsonr
import calendar
import sqlite3
import pydot
import pdb
import json
import networkx as nx
import pylab as py

# Open the database
conn = sqlite3.connect("/Users/cbogart/rscraper/repoScrape.db")  # "githubR.bak.db")
conn.row_factory = sqlite3.Row
conn.execute("pragma short_column_names=OFF;");
conn.execute("pragma full_column_names=ON;");

# Fixed sql statements
filesColumns = "file_id, project_id, path, size, last_edit, retrieved, " + \
               "repos, cb_last_scan, error"
insertFilesSQL = "insert into files (" + filesColumns + ") values (" + \
               "?,?,?,?,?,?,?,?,?);"
importsColumns = "file_id, project_id, package_name, cb_last_scan"
insertImportsSQL = "insert into imports (" + importsColumns + ") values (" + \
               "?,?,?,?);"


def allpackagesByTask(pattern):
    cur = conn.cursor()
    cur.execute("select package_name pack, count(distinct(project_id)) occs from gitimports where package_name in (select package_name from tags where tag like '%" + pattern + "%') group by package_name;")
    return set([p['pack'].strip() for p in cur.fetchall()])


def allpackages(minInstances):
    cur = conn.cursor()
    cur.execute("select package_name pack, count(distinct(project_id)) occs from gitimports group by package_name having occs >= ?;", (minInstances,))
    return set([p['pack'].strip() for p in cur.fetchall()])

def loadCategories():
    with open("categories.json", "r") as f:
        categB = json.loads(f.read())
    with open("categoriescran.json", "r") as f:
        categC = json.loads(f.read())
    node2categ = dict(categB.items() + categC.items())
    
    categ = defaultdict(int)
    for n in node2categ:
        for c in node2categ[n]["views"]: categ[c] += 1
    
    for n in node2categ:
        bestc = ""
        bestccount = 99999
        for c in node2categ[n]["views"]:
            if categ[c] < bestccount:
                bestc = c
                bestccount = categ[c]
        node2categ[n]["bestview"] = bestc
        node2categ[n]["color"] = hashColor(bestc)
    
    return node2categ

def hashColor(key, selected=False):
    """Return a color unique for this key, brigher if selected.

    Of course the color can't really be unique because there are more keys
    in the world than colors; but the algorithm tries to make similar strings
    come out different colors so they can be distinguished in a chart or graph"""

    def tw(t): return t ^ (t << (t % 5)) ^ (t << (6 + (t % 7))) ^ (t << (13 + (t % 11)))
    theHash = tw(hash(key) % 5003)
    ifsel = 0x00 if selected else 0x80
    (r, g, b) = (ifsel | (theHash & 0x7f),
               ifsel | ((theHash >> 8) & 0x7F),
               ifsel | ((theHash >> 16) & 0x7F))
    return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

def mutInfNumpy(allpacks):
    otherpacks = allpacks.copy()
    
    arrays = defaultdict(numpy.array)
    
    categories = loadCategories()
    
    def colorOfFull(pkg):
        views = categories.get(pkg, { "views": [] })["views"]
        color = ",".join(sorted(views))
        return hashColor(color)
    def colorOfBestview(pkg):
        return categories.get(pkg, {"color": "#808080"})["color"]
    def colorOfRepo(pkg): 
        return hashColor(categories.get(pkg, {"repos": "other"})["repos"])
    def colorOfOptimization(pkg):
        views = categories.get(pkg, {"views": []})["views"] 
        if "Optimization" in views:
            return "#4040ff"
        # elif "Finance" in views or "Econometrics" in views:
        #    return "#80ffff"
        else:
            return colorOfRepo(pkg)  # "#ff80ff"
    
    def colorOf(pkg): return colorOfOptimization(pkg)
      

    try:
        with open('mi.pickle') as f:
            [G, arrays] = pickle.load(f)
    except:
        cur = conn.cursor()
        cur.execute("select project_id, group_concat(distinct(package_name)) packs from gitimports group by project_id")
        imps = cur.fetchall()
        for p in allpacks:
            arrays[p] = numpy.array([0] * len(imps))
        rowid = 0
        for imp in imps:
            packs = set([p.strip() for p in imp['packs'].split(",")])
            for p in allpacks:
                arrays[p][rowid] = 1 if p in packs else 0
            rowid += 1 
    
        G = nx.Graph()
        checked = 0
        print "Checking ", len(otherpacks) * len(otherpacks), "package pairs"
        for o1 in otherpacks:
            checked = checked + len(otherpacks)
            print "Checked", checked
            for o2 in otherpacks:
                if (o1 < o2):
                    mis = nPMI(arrays[o1], arrays[o2])
                    if mis > .2: 
                        G.add_node(o1, color=colorOf(o1))
                        G.add_node(o2, color=colorOf(o2))
                        G.add_edge(o1, o2, weight=mis * 10)
                        print o1, o2, mis  # , "\tCorrelation is", pearsonr(arrays[o1], arrays[o2])
        with open('mi.pickle', 'w') as f:
            pickle.dump([G, arrays], f)
    
    def fix(n): return n if n != "graphx" else "graph"
    
    G = nx.relabel_nodes(G, {"graph": "graphx"})
    sizes = [30 + 100 * math.sqrt(numpy.sum(arrays[fix(n)])) for n in G.nodes()]
    colors = [colorOf(fix(i)) for i in G.nodes()]
    labels = { i: i + ("\n" + categories[fix(i)]["bestview"] if i in categories and categories[fix(i)]["bestview"] != "" else "") for i in G.nodes()}
    # nx.draw_spring(G, with_labels=True, weight="weight", node_color=colors, node_size = sizes, iterations=15000)
    nx.draw_graphviz(G, prog="neato", with_labels=True, weight="weight", node_color=colors, labels=labels, iterations=1500, node_size=sizes)
    py.show()
   
def nPMI(array1, array2):
    N = len(array1)
    pxy = (sum(array1 * array2) * 1.0 / N)
    px = sum(array1) * 1.0 / N
    py = sum(array2) * 1.0 / N
    if pxy == 0 or px == 0 or py == 0:
        pmi = -1
    else:
        pmi = -math.log(pxy / (px * py)) / math.log(pxy)
    return pmi
      

def commonestPair():
    cur = conn.cursor()
    
    cur.execute("select project_id, group_concat(distinct(package_name)) packs from gitimports group by project_id")
    imps = cur.fetchall()
    pairs = defaultdict(int)
    for imp in imps:
        packs = set([p.strip() for p in imp['packs'].split(",")])
        for p1 in packs:
            for p2 in packs:
                if (p1 != p2):
                    pairs[",".join([p1, p2])] += 1
    maxpair = ""
    maxpairval = 0
    for p in pairs:
        if pairs[p] > maxpairval:
            maxpairval = pairs[p]
            maxpair = p
    print "Max pair is", maxpair, "happening", maxpairval, "times"
   


if "__main__" == __name__:
    allpacks = allpackages(5)
    mutInfNumpy(allpacks)
